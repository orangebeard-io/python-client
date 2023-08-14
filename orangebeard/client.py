from datetime import datetime
from pytz import reference

from uuid import UUID

import urllib3
import json

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
client = urllib3.PoolManager()
LOG_BUFFER = 10


class OrangebeardClient:
    """Orangebeard client for Python integrations"""

    def __init__(self, endpoint, accessToken, project, testrunUUID=None, **_):
        """Initialize Orangebeard client

        :param endpoint:    Your orangebeard.app URL
        :param accessToken: The listener token for the reporting user
        :param project:     The Orangebeard project to report to
        :param testrunUUID: The (Optional) UUID of the (announced) testrun to report to
        """
        self.logstack = {}
        self.logUuidMap = {}
        self.endpoint = endpoint
        self.accessToken = accessToken
        self.project = project
        self.testrunUUID = testrunUUID

    def getHeaders(self, contentType):
        return {
            "Authorization": "Bearer {0}".format(self.accessToken),
            "Content-Type": "{0}".format(contentType),
        }

    def startTestrun(
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
        url = "{0}/listener/v3/{1}/test-run/start".format(self.endpoint, self.project)

        response = client.request(
            "POST",
            url,
            body=startRun.toJson(),
            headers=self.getHeaders("application/json"),
        )

        responseJson = json.loads(response.data.decode("utf-8"))
        self.testrunUUID = responseJson["testRunUUID"]

        return UUID(self.testrunUUID)

    def startAnnouncedTestrun(self, testRunUUID: UUID):
        """Start a previously announced testrun.

        :param testRunUUID: The UUID of the test run to start
        """

        url = "{0}/listener/v3/{1}/test-run/start/{2}".format(
            self.endpoint, self.project, testRunUUID
        )
        client.request("PUT", url, headers=self.getHeaders("application/json"))

    def finishTestRun(self, testRunUUID: UUID, endTime=None):
        """Finish a testrun by UUID

        :param testRunUUID: The UUID of the run to finish
        :param endTime:     The end date
        """
        self.flushLogStack()
        finishRun = FinishTestRun(endTime or datetime.now(tz))

        url = "{0}/listener/v3/{1}/test-run/finish/{2}".format(
            self.endpoint, self.project, testRunUUID
        )
        client.request(
            "PUT",
            url,
            body=finishRun.toJson(),
            headers=self.getHeaders("application/json"),
        )

    def startSuite(
        self,
        testRunUUID: UUID,
        suiteNames,
        parentSuiteUUID: UUID = None,  # type: ignore
        description=None,
        attributes=None,
    ):
        startSuite = StartSuite(
            testRunUUID, suiteNames, parentSuiteUUID, description, attributes
        )
        url = "{0}/listener/v3/{1}/suite/start".format(self.endpoint, self.project)

        response = client.request(
            "POST",
            url,
            body=startSuite.toJson(),
            headers=self.getHeaders("application/json"),
        )
        responseJson = json.loads(response.data.decode("utf-8"))
        return responseJson

    def startTest(
        self,
        testRunUUID: UUID,
        suiteUUID: UUID,
        name,
        testType: TestType,
        attributes=[],
        description=None,
        startTime=None,
    ) -> UUID:
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

        response = client.request(
            "POST",
            url,
            body=startTest.toJson(),
            headers=self.getHeaders("application/json"),
        )
        responseJson = json.loads(response.data.decode("utf-8"))

        return UUID(responseJson["getTestUUID"])

    def finishTest(self, testUUID, testRunUUID, status: TestStatus, endTime=None):
        finishTest = FinishTest(testRunUUID, status, endTime or datetime.now(tz))
        url = "{0}/listener/v3/{1}/test/finish/{2}".format(
            self.endpoint, self.project, testUUID
        )

        client.request(
            "PUT",
            url,
            body=finishTest.toJson(),
            headers=self.getHeaders("application/json"),
        )

    def startStep(
        self,
        testRunUUID: UUID,
        testUUID: UUID,
        stepName,
        parentStepUUID: UUID = None,  # type: ignore
        description=None,
        startTime=None,
    ) -> UUID:
        startStep = StartStep(
            testRunUUID,
            testUUID,
            parentStepUUID,
            stepName,
            startTime or datetime.now(tz),
            description,
        )
        url = "{0}/listener/v3/{1}/step/start".format(self.endpoint, self.project)

        response = client.request(
            "POST",
            url,
            body=startStep.toJson(),
            headers=self.getHeaders("application/json"),
        )
        responseJson = json.loads(response.data.decode("utf-8"))

        return UUID(responseJson["stepUUID"])

    def finishStep(
        self,
        stepUUID: UUID,
        testRunUUID: UUID,
        status: TestStatus,
        endTime=None,
    ):
        finishStep = FinishStep(testRunUUID, status, endTime or datetime.now(tz))
        url = "{0}/listener/v3/{1}/step/finish/{2}".format(
            self.endpoint, self.project, stepUUID
        )

        client.request(
            "PUT",
            url,
            body=finishStep.toJson(),
            headers=self.getHeaders("application/json"),
        )

    def log(
        self,
        testRunUUID: UUID,
        testUUID: UUID,
        logLevel: LogLevel,
        message,
        stepUUID: UUID = None,  # type: ignore
        logTime=None,
        logFormat=LogFormat.PLAIN_TEXT,
    ) -> UUID:
        logItem = Log(
            testRunUUID,
            testUUID,
            message,
            logLevel,
            logFormat,
            stepUUID,
            logTime or datetime.now(tz),
        )
        temp_id = UUID()
        self.logstack[temp_id] = logItem

        if len(self.logstack) >= LOG_BUFFER:
            self.flushLogStack()

        return temp_id

    def logAttachment(
        self, attachmentFile: AttachmentFile, attachmentMetaData: AttachmentMetaData
    ) -> UUID:
        realUUID = self.logUuidMap.get(attachmentMetaData.logUUID) or None
        if realUUID == None:
            self.flushLogStack()
            realUUID = self.logUuidMap.get(attachmentMetaData.logUUID)

        attachmentMetaData.logUUID = str(realUUID)

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

        headers = self.getHeaders(contentType)

        response = client.request("POST", url, body=body, headers=headers)
        responseJson = json.loads(response.data.decode("utf-8"))

        return UUID(responseJson["attachmentUUID"])

    def flushLogStack(self):
        logIds = list(self.logstack.keys())
        logItems = list(self.logstack.values())
        url = "{0}/listener/v3/{1}/log/batch".format(self.endpoint, self.project)

        response = client.request(
            "POST",
            url,
            body=json.dumps(logItems),
            headers=self.getHeaders("application/json"),
        )
        responseJson = json.loads(response.data.decode("utf-8"))
        reportedLogs = {
            logIds[i]: UUID(responseJson[i]["logUUID"]) for i in range(len(logIds))
        }
        self.logUuidMap.update(reportedLogs)
        self.logstack.clear()
