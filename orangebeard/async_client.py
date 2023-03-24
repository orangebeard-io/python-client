import asyncio
from datetime import datetime
from pytz import reference
import aiohttp
from uuid import UUID, uuid4

import urllib3

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
    temp_UUIDS = {}

    def __init__(self, endpoint, accessToken, project, testrunUUID=None, **_):
        """Initialize Orangebeard client

        :param endpoint:    Your orangebeard.app URL
        :param accessToken: The listener token for the reporting user
        :param project:     The Orangebeard project to report to
        :param testrunUUID: The (Optional) UUID of the (announced) testrun to report to
        """

        self.endpoint = endpoint
        self.accessToken = accessToken
        self.project = project
        self.testrunUUID: testrunUUID # type: ignore

    def getHeaders(self, contentType):
        return {
            "Authorization": "Bearer {0}".format(self.accessToken),
            "Content-Type": "{0}".format(contentType),
        }

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

        temp_id = uuid4()

        startRun = StartTestRun(
            testSetName,
            startTime or datetime.now(tz),
            description,
            attributes,
            changedComponents,
        )
        url = "{0}/listener/v3/{1}/test-run/start".format(self.endpoint, self.project)

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            async with session.post(url, data=startRun.toJson()) as response:
                response_data = await response.json()
                self.testrunUUID = UUID(response_data["testRunUUID"])
                self.temp_UUIDS[temp_id] = self.testrunUUID

        return temp_id

    async def startAnnouncedTestrun(self, testRunUUID: UUID):
        """Start a previously announced testrun.

        :param testRunUUID: The UUID of the test run to start
        """

        url = "{0}/listener/v3/{1}/test-run/start/{2}".format(
            self.endpoint, self.project, testRunUUID
        )

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            async with session.put(url) as response:
                await response.json()

        self.testrunUUID = testRunUUID

    async def finishTestRun(self, tempTestRunUUID: UUID, endTime=None):
        """Finish a testrun by UUID

        :param testRunUUID: The UUID of the run to finish
        :param endTime:     The end date
        """

        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        finishRun = FinishTestRun(endTime or datetime.now(tz))

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/test-run/finish/{2}".format(
                self.endpoint, self.project, testRunUUID
            )
            await session.put(url, data=finishRun.toJson())

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
            temp_ids.append(uuid4())

        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        parentSuiteUUID = (
            await self.getRealUUIDForTempId(tempParentSuiteUUID)
            if tempParentSuiteUUID
            else None
        )
        startSuite = StartSuite(
            testRunUUID, suiteNames, parentSuiteUUID, description, attributes  # type: ignore
        )

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/suite/start".format(self.endpoint, self.project)

            async with session.post(url, data=startSuite.toJson()) as response:
                response_data = await response.json()
                uuids = {temp_ids[i]: response_data[i]['suiteUUID'] for i in range(0, len(temp_ids)-1)}
                self.temp_UUIDS.update(uuids)

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
        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        suiteUUID = await self.getRealUUIDForTempId(tempSuiteUUID)
        startTest = StartTest(
            testRunUUID,
            suiteUUID,
            name,
            startTime or datetime.now(tz),
            testType,
            description,
            attributes,
        )

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/test/start".format(self.endpoint, self.project)

            async with session.post(url, data=startTest.toJson()) as response:
                response_data = await response.json()
                self.temp_UUIDS[temp_id] = UUID(response_data["getTestUUID"])

        return temp_id

    async def finishTest(
        self, tempTestUUID, tempTestRunUUID, status: TestStatus, endTime=None
    ):
        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        testUUID = await self.getRealUUIDForTempId(tempTestUUID)
        finishTest = FinishTest(testRunUUID, status, endTime or datetime.now(tz))
        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/test/finish/{2}".format(
                self.endpoint, self.project, testUUID
            )
            await session.put(url, data=finishTest.toJson())

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
        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        testUUID = await self.getRealUUIDForTempId(tempTestUUID)
        parentStepUUID = (
            await self.getRealUUIDForTempId(tempParentStepUUID)
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

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/step/start".format(self.endpoint, self.project)

            async with session.post(url, data=startStep.toJson()) as response:
                response_data = await response.json()
                self.temp_UUIDS[temp_id] = UUID(response_data["stepUUID"])

        return temp_id

    async def finishStep(
        self,
        tempStepUUID: UUID,
        tempTestRunUUID: UUID,
        status: TestStatus,
        endTime=None,
    ):
        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        stepUUID = await self.getRealUUIDForTempId(tempStepUUID)

        finishStep = FinishStep(testRunUUID, status, endTime or datetime.now(tz))

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/step/finish/{2}".format(
                self.endpoint, self.project, stepUUID
            )
            await session.put(url, data=finishStep.toJson()) 

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
        testRunUUID = await self.getRealUUIDForTempId(tempTestRunUUID)
        testUUID = await self.getRealUUIDForTempId(tempTestUUID)
        stepUUID = await self.getRealUUIDForTempId(tempStepUUID) if tempStepUUID else None

        logItem = Log(
            testRunUUID,
            testUUID,
            message,
            logLevel,
            logFormat,
            stepUUID,
            logTime or datetime.now(tz),
        )

        async with aiohttp.ClientSession(
            headers=self.getHeaders("application/json")
        ) as session:
            url = "{0}/listener/v3/{1}/log".format(self.endpoint, self.project)

            async with session.post(url, data=logItem.toJson()) as response:
                response_data = await response.json()
                self.temp_UUIDS[temp_id] = UUID(response_data["logUUID"])

        return temp_id

    async def logAttachment(
        self, attachmentFile: AttachmentFile, attachmentMetaData: AttachmentMetaData
    ) -> UUID:
        temp_id = uuid4()

        testRunUUID = await self.getRealUUIDForTempId(
            UUID(attachmentMetaData.testRunUUID)
        )
        testUUID = await self.getRealUUIDForTempId(UUID(attachmentMetaData.testUUID))
        stepUUID = await self.getRealUUIDForTempId(UUID(attachmentMetaData.stepUUID))
        logUUID = await self.getRealUUIDForTempId(UUID(attachmentMetaData.logUUID))

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

        async with aiohttp.ClientSession(
            headers=self.getHeaders(contentType)
        ) as session:
            url = "{0}/listener/v3/{1}/attachment".format(self.endpoint, self.project)

            async with session.post(url, data=body) as response:
                response_data = await response.json()
                self.temp_UUIDS[temp_id] = UUID(response_data["attachmentUUID"])

        return temp_id

    async def getRealUUIDForTempId(self, tempId: UUID) -> UUID:
        waittime = 0
        while self.temp_UUIDS[tempId] is None and waittime < 100:
            await asyncio.sleep(0.1)
            waittime = waittime + 1

        return self.temp_UUIDS[tempId]