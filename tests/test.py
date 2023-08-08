import asyncio
from orangebeard.async_client import AsyncOrangebeardClient
from orangebeard.client import OrangebeardClient
from orangebeard.entity.Attachment import AttachmentFile, AttachmentMetaData
from orangebeard.entity.TestStatus import TestStatus
from orangebeard.entity.TestType import TestType
from orangebeard.entity.LogLevel import LogLevel

from datetime import datetime


# endpoint = 'https://test.orangebeard-staging.app'
# token = 'b514a716-93d8-11ec-98ed-422f0523bd0e'
# project = 'listeners'

endpoint = 'https://demo.orangebeard-staging.app'
token = '98d88993-ccec-4778-866a-805c9f6ea1d1'
project = 'tomheintzberger_personal'


async def main():
    client = AsyncOrangebeardClient(endpoint, token, project)
    
    starttime = datetime.now()
    print('Start: {0}', starttime.timestamp())
    testRunUUID = await client.startTestrun('Python client test')
    print('Started run: {0}\n'.format(testRunUUID))

    suiteNames =  ['Top Level Suite', 'Level 2 Suite']
    suiteUUIDs = await client.startSuite(testRunUUID, suiteNames)
    print('\tStarted suite: {0}\n'.format(suiteUUIDs))

    testUUID = await client.startTest(testRunUUID, suiteUUIDs[0], "Test 1", TestType.TEST)
    print('\tStarted test: {0}\n'.format(testUUID))

    stepUUID = await client.startStep(testRunUUID, testUUID, 'Test step 1')
    print('\tStarted step: {0}\n'.format(stepUUID))

    step2UUID = await client.startStep(testRunUUID, testUUID, 'Test step 2')
    print('\tStarted substep: {0}\n'.format(stepUUID))

    logUUID = await client.log(testRunUUID, testUUID, LogLevel.INFO, 'Some more informational log', step2UUID)

    logUUID2 = await client.log(testRunUUID, testUUID, LogLevel.INFO, 'Some informational log', stepUUID)
    print('\tLog sent: {0}\n'.format(logUUID))

    attachmentFile = AttachmentFile('logo.svg', open('./.github/logo.svg', 'rb').read())
    attachmentMeta = AttachmentMetaData(testRunUUID, testUUID, logUUID, stepUUID)

    attachmentUUID = await client.logAttachment(attachmentFile, attachmentMeta)
    print('\tAttached file to log - Attachment: {0}\n'.format(attachmentUUID))

    await client.finishStep(step2UUID, testRunUUID, TestStatus.PASSED)
    await client.finishStep(stepUUID, testRunUUID, TestStatus.PASSED)

    await  client.finishTest(testUUID, testRunUUID, TestStatus.PASSED)

    await client.finishTestRun(testRunUUID)
    endtime = datetime.now()
    print('Finish: {0}', endtime.timestamp())

    elapsed = endtime-starttime
    print('Elapsed: {0}', elapsed)

import platform
if platform.system()=='Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())