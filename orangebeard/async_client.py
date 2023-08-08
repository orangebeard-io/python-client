import asyncio
from datetime import datetime
from pytz import reference
import aiohttp
from uuid import UUID, uuid4

import urllib3
import json
import time

import traceback

from orangebeard.entity.FinishStep import FinishStep
from orangebeard.entity.LogLevel import LogLevel
from orangebeard.entity.StartStep import StartStep
from orangebeard.entity.Attachment import AttachmentFile, AttachmentMetaData
from orangebeard.entity.LogFormat import LogFormat
from orangebeard.entity.StartTestRun import StartTestRun
from orangebeard.entity.FinishTestRun import FinishTestRun
from orangebeard.entity.StartSuite import StartSuite
from orangebeard.entity.StartTest import StartTest
from orangebeard.entity.StartStep import StartStep
from orangebeard.entity.TestType import TestType
from orangebeard.entity.FinishTest import FinishTest
from orangebeard.entity.TestStatus import TestStatus
from orangebeard.entity.Log import Log

tz = reference.LocalTimezone()

class AsyncOrangebeardClient:
    def __init__(self, endpoint, accessToken, project, testrunUUID=None, logBuffer = 10, **_):
        """Initialize Orangebeard client

        :param endpoint:    Your orangebeard.app URL
        :param accessToken: The listener token for the reporting user
        :param project:     The Orangebeard project to report to
        :param testrunUUID: The (Optional) UUID of the (announced) testrun to report to
        """

        self.log_buffer = logBuffer
        self.endpoint = endpoint
        self.access_token = accessToken
        self.project = project
        self.test_run_uuid: testrunUUID  # type: ignore
        self.temp_uuids = {}
        self.logstack = {}

    def _get_headers(self, contentType):
        return {
            "Authorization": "Bearer {0}".format(self.access_token),
            "Content-Type": "{0}".format(contentType),
        }

    async def _perform_request(
        self, method, url, body=None, contentType="application/json"
    ):
        async with aiohttp.ClientSession(
            headers=self._get_headers(contentType)
        ) as session:
            async with session.request(method, url, data=body) as response:
                return None if method == "PUT" else await response.json()

    async def _store_real_uuid(self, tempUUID, response, uuidKey=None):
        if uuidKey is None:
            self.temp_uuids[tempUUID] = UUID(response)
        else:
            self.temp_uuids[tempUUID] = UUID(response[uuidKey])

    async def _store_real_suite_uuids(self, tempUUIDList, response_data):
        tempUUIDList.reverse()
        for i, tempUUID in enumerate(tempUUIDList):
            self.temp_uuids[tempUUID] = response_data[i]["suiteUUID"]

    async def _store_real_log_uuids(self, tempUUIDList, response_data):
        for i, tempUUID in enumerate(tempUUIDList):
            self.temp_uuids[tempUUID] = response_data[i]

    async def _get_real_uuid_for_temp_id(self, tempId: UUID) -> UUID:
        starttime = time.time()
        while self.temp_uuids[tempId] is None and time.time() <= starttime + 30:
            await asyncio.sleep(0.01)
        
        return self.temp_uuids[tempId]
        

    async def startTestrun(
        self,
        testSetName,
        startTime=None,
        description=None,
        attributes=[],
        changedComponents=[],
    ) -> UUID:
        """Start a testrun.

        :param name:        The name of the testset that is being run
        :param startTime:   The start time of the test run
        :param description: The description of the test run
        :param attrbutes:   Attributes to save with this test run
        """

        startRun = StartTestRun(
            testSetName,
            startTime or datetime.now(tz),
            description,
            attributes,
            changedComponents,
        )
        temp_id = uuid4()
        self.temp_uuids[temp_id] = None

        url = "{0}/listener/v3/{1}/test-run/start".format(self.endpoint, self.project)

        response = await self._perform_request("POST", url, startRun.toJson())
        await self._store_real_uuid(temp_id, response)

        return temp_id

    async def startAnnouncedTestrun(self, testRunUUID: UUID):
        """Start a previously announced testrun.
        :param testRunUUID: The UUID of the test run to start
        """

        url = "{0}/listener/v3/{1}/test-run/start/{2}".format(
            self.endpoint, self.project, testRunUUID
        )

        await self._perform_request("PUT", url)

        self.test_run_uuid = testRunUUID

    async def finishTestRun(self, tempTestRunUUID: UUID, endTime=None):
        """Finish a testrun by UUID

        :param testRunUUID: The UUID of the run to finish
        :param endTime:     The end date
        """
        asyncio.create_task(self.flushLogStack())

        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        finishRun = FinishTestRun(endTime or datetime.now(tz))

        url = "{0}/listener/v3/{1}/test-run/finish/{2}".format(
            self.endpoint, self.project, testRunUUID
        )

        all_tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()
        all_tasks.remove(current_task)  # type: ignore
        await asyncio.gather(*all_tasks)
        await self._perform_request("PUT", url, finishRun.toJson())


    async def startSuite(
        self,
        tempTestRunUUID: UUID,
        suiteNames,
        tempParentSuiteUUID: UUID = None,  # type: ignore
        description=None,
        attributes=None,
    ) -> list:
        temp_ids = []
        for i in range(len(suiteNames)):
            temp_id = uuid4()
            temp_ids.append(temp_id)
            self.temp_uuids[temp_id] = None

        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        parentSuiteUUID = (
            None
            if tempParentSuiteUUID is None
            else await asyncio.create_task(
                self._get_real_uuid_for_temp_id(tempParentSuiteUUID)
            )
        )

        startSuite = StartSuite(
            testRunUUID, suiteNames, parentSuiteUUID, description, attributes  # type: ignore
        )

        url = "{0}/listener/v3/{1}/suite/start".format(self.endpoint, self.project)

        asyncio.create_task(
            self._perform_request("POST", url, startSuite.toJson())
        ).add_done_callback(
            lambda f: asyncio.create_task(
                self._store_real_suite_uuids(temp_ids, f.result())
            )
        )

        return temp_ids

    async def startTest(
        self,
        tempTestRunUUID: UUID,
        tempSuiteUUID: UUID,
        name,
        testType: TestType,
        attributes=[],
        description=None,
        startTime=None,
    ) -> UUID:
        temp_id = uuid4()
        self.temp_uuids[temp_id] = None

        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        suiteUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempSuiteUUID)
        )
        startTest = StartTest(
            testRunUUID,
            suiteUUID,
            name,
            startTime or datetime.now(tz),
            testType,
            description,
            attributes,
        )

        url = "{0}/listener/v3/{1}/test/start".format(self.endpoint, self.project)

        response = await self._perform_request("POST", url, startTest.toJson())
        await self._store_real_uuid(temp_id, response)

        return temp_id

    async def finishTest(
        self, tempTestUUID, tempTestRunUUID, status: TestStatus, endTime=None
    ):
        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        testUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestUUID)
        )
        finishTest = FinishTest(testRunUUID, status, endTime or datetime.now(tz))
        url = "{0}/listener/v3/{1}/test/finish/{2}".format(
            self.endpoint, self.project, testUUID
        )

        asyncio.create_task(self._perform_request("PUT", url, finishTest.toJson()))

    async def startStep(
        self,
        tempTestRunUUID: UUID,
        tempTestUUID: UUID,
        stepName,
        tempParentStepUUID: UUID = None,  # type: ignore
        description=None,
        startTime=None,
    ) -> UUID:
        temp_id = uuid4()
        self.temp_uuids[temp_id] = None

        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        testUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestUUID)
        )

        parentStepUUID = (
            await asyncio.create_task(
                self._get_real_uuid_for_temp_id(tempParentStepUUID)
            )
            if tempParentStepUUID
            else None
        )
        startStep = StartStep(
            testRunUUID,
            testUUID,
            parentStepUUID,  # type: ignore
            stepName,
            startTime or datetime.now(tz),
            description,
        )

        url = "{0}/listener/v3/{1}/step/start".format(self.endpoint, self.project)

        response = await self._perform_request("POST", url, startStep.toJson())
        await self._store_real_uuid(temp_id, response)

        return temp_id

    async def finishStep(
        self,
        tempStepUUID: UUID,
        tempTestRunUUID: UUID,
        status: TestStatus,
        endTime=None,
    ):
        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        stepUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempStepUUID)
        )

        finishStep = FinishStep(testRunUUID, status, endTime or datetime.now(tz))

        url = "{0}/listener/v3/{1}/step/finish/{2}".format(
            self.endpoint, self.project, stepUUID
        )

        await asyncio.create_task(self._perform_request("PUT", url, finishStep.toJson()))

    async def log(
        self,
        tempTestRunUUID: UUID,
        tempTestUUID: UUID,
        logLevel: LogLevel,
        message,
        tempStepUUID: UUID = None,  # type: ignore
        logTime=None,
        logFormat=LogFormat.PLAIN_TEXT,
    ) -> UUID:
        temp_id = uuid4()
        self.temp_uuids[temp_id] = None

        testRunUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestRunUUID)
        )
        testUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(tempTestUUID)
        )
        stepUUID = (
            await asyncio.create_task(self._get_real_uuid_for_temp_id(tempStepUUID))
            if tempStepUUID
            else None
        )

        logItem = Log(
            testRunUUID,
            testUUID,
            message,
            logLevel,
            logFormat,
            stepUUID,
            logTime or datetime.now(tz),
        )

        self.logstack[temp_id] = logItem

        if len(self.logstack) >= self.log_buffer:
            await asyncio.create_task(self.flushLogStack())

        return temp_id

    async def logAttachment(
        self, attachmentFile: AttachmentFile, attachmentMetaData: AttachmentMetaData
    ) -> UUID:
        temp_id = uuid4()
        self.temp_uuids[temp_id] = None

        testRunUUID = await self._get_real_uuid_for_temp_id(
            UUID(attachmentMetaData.testRunUUID)
        )

        await asyncio.create_task(self.flushLogStack())

        testUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(UUID(attachmentMetaData.testUUID))
        )
        stepUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(UUID(attachmentMetaData.stepUUID))
        )
        logUUID = await asyncio.create_task(
            self._get_real_uuid_for_temp_id(UUID(attachmentMetaData.logUUID))
        )

        attachmentMetaData.testRunUUID = str(testRunUUID)
        attachmentMetaData.testUUID = str(testUUID)
        attachmentMetaData.stepUUID = str(stepUUID)
        attachmentMetaData.logUUID = str(logUUID)

        payload = {
            "json": attachmentMetaData.toJson(),
            "attachment": (
                attachmentFile.name,
                attachmentFile.content,
                attachmentFile.contentType,
            ),
        }

        body, contentType = urllib3.encode_multipart_formdata(payload)

        url = "{0}/listener/v3/{1}/attachment".format(self.endpoint, self.project)
        response = await self._perform_request("POST", url, body, contentType)
        await self._store_real_uuid(temp_id, response)

        return temp_id

    async def flushLogStack(self):
        logIds = list(self.logstack.keys())
        logItems = list(self.logstack.values())
        self.logstack.clear()

        url = "{0}/listener/v3/{1}/log/batch".format(self.endpoint, self.project)
        response = await self._perform_request(
            "POST", url, json.dumps(logItems, default=lambda o: o.__dict__)
        )
        await self._store_real_log_uuids(logIds, response)
