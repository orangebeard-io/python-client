
from datetime import datetime
from pytz import reference
from orangebeard.client import OrangebeardClient
from orangebeard.entity.Attachment import AttachmentFile, AttachmentMetaData
from orangebeard.entity.TestStatus import TestStatus
from orangebeard.entity.TestType import TestType
from orangebeard.entity.LogLevel import LogLevel

# endpoint = 'https://test.orangebeard-staging.app'
# token = 'b514a716-93d8-11ec-98ed-422f0523bd0e'
# project = 'listeners'

endpoint = 'https://demo.orangebeard-staging.app'
token = '98d88993-ccec-4778-866a-805c9f6ea1d1'
project = 'tomheintzberger_personal'

tz = reference.LocalTimezone()

client = OrangebeardClient(endpoint, token, project)
testRunUUID = client.startTestrun('Python client test')
print('Started run: {0}\n'.format(testRunUUID))

suiteUUIDs = client.startSuite(testRunUUID, ['Top Level Suite', 'Level 2 Suite'])
print('\tStarted suite: {0}\n'.format(suiteUUIDs))

testUUID = client.startTest(testRunUUID, suiteUUIDs[0]['suiteUUID'], "Test 1", TestType.TEST)
print('\tStarted test: {0}\n'.format(testUUID))

stepUUID = client.startStep(testRunUUID, testUUID, 'Test step 1')
print('\tStarted step: {0}\n'.format(stepUUID))

logUUID = client.log(testRunUUID, testUUID, LogLevel.INFO, 'Some informational log', stepUUID)
print('\tLog sent: {0}\n'.format(logUUID))

attachmentFile = AttachmentFile('README.MD', open('README.MD', 'rb').read(), 'text/plain')
attachmentMeta = AttachmentMetaData(testRunUUID, testUUID, logUUID, stepUUID, datetime.now(tz))

attachmentUUID = client.logAttachment(attachmentFile, attachmentMeta)
print('\tAttached file to log - Attachment: {0}\n'.format(attachmentUUID))

client.finishStep(stepUUID, testRunUUID, TestStatus.PASSED)

client.finishTest(testUUID, testRunUUID, TestStatus.PASSED)

client.finishTestRun(testRunUUID)