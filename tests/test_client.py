import asyncio
import uuid
from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, patch

from orangebeard.OrangebeardClient import OrangebeardClient
from orangebeard.entity.StartTestRun import StartTestRun
from orangebeard.entity.FinishTestRun import FinishTestRun
from orangebeard.entity.StartSuite import StartSuite
from orangebeard.entity.StartTest import StartTest
from orangebeard.entity.FinishTest import FinishTest
from orangebeard.entity.StartStep import StartStep
from orangebeard.entity.FinishStep import FinishStep
from orangebeard.entity.Log import Log
from orangebeard.entity.Attachment import Attachment, AttachmentFile, AttachmentMetaData
from orangebeard.entity.TestType import TestType
from orangebeard.entity.TestStatus import TestStatus
from orangebeard.entity.LogFormat import LogFormat
from orangebeard.entity.LogLevel import LogLevel

class DummyResponse:
    def __init__(self, status=200, json_data=None, text=''):
        self.status = status
        self._json_data = json_data
        self._text = text
    async def json(self):
        return self._json_data
    async def text(self):
        return self._text
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass

class DummyClientSession:
    def __init__(self, response=None, *args, **kwargs):
        self._response = response or DummyResponse()
        self.closed = False
    def request(self, *args, **kwargs):
        return self._response
    async def close(self):
        self.closed = True

class TestOrangebeardClient(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('orangebeard.OrangebeardClient.aiohttp.ClientSession', DummyClientSession)
        self.patcher.start()
        self.client = OrangebeardClient(endpoint='http://localhost', access_token=uuid.uuid4(), project_name='proj')
        self.client._OrangebeardClient__client = DummyClientSession()

    def tearDown(self):
        self.patcher.stop()
        loop = self.client._OrangebeardClient__event_loop
        if not loop.is_closed():
            loop.run_until_complete(self.client._OrangebeardClient__client.close())
            loop.close()

    def test_start_test_run(self):
        actual_uuid = str(uuid.uuid4())
        self.client._OrangebeardClient__make_api_request = AsyncMock(return_value=actual_uuid)
        start = StartTestRun('set', datetime.now(timezone.utc), 'desc')
        temp_uuid = self.client.start_test_run(start)
        self.assertEqual(self.client._OrangebeardClient__uuid_mapping[temp_uuid], actual_uuid)
        self.assertTrue(self.client._OrangebeardClient__call_events[temp_uuid].is_set())

    def test_start_announced_test_run(self):
        self.client._OrangebeardClient__make_api_request = AsyncMock(return_value=None)
        tr_uuid = uuid.uuid4()
        self.client.start_announced_test_run(tr_uuid)
        self.assertEqual(self.client._OrangebeardClient__uuid_mapping[tr_uuid], tr_uuid)
        self.assertTrue(self.client._OrangebeardClient__call_events[tr_uuid].is_set())

    def test_start_suite(self):
        self.client._OrangebeardClient__make_api_request = AsyncMock(side_effect=[str(uuid.uuid4()), [{'suiteUUID': 'real'}]])
        start_run = StartTestRun('set', datetime.now(timezone.utc), 'desc')
        run_uuid = self.client.start_test_run(start_run)
        suite = StartSuite(run_uuid, ['suite'])
        suite_temp = self.client.start_suite(suite)
        self.assertEqual(self.client._OrangebeardClient__uuid_mapping[suite_temp[0]], 'real')
        self.assertTrue(self.client._OrangebeardClient__call_events[suite_temp[0]].is_set())

    def test_start_test_and_finish_test(self):
        # Start run and suite first
        self.client._OrangebeardClient__make_api_request = AsyncMock(side_effect=[str(uuid.uuid4()), [{'suiteUUID': 'real-suite'}], 'real-test', None])
        start_run = StartTestRun('set', datetime.now(timezone.utc), 'desc')
        run_uuid = self.client.start_test_run(start_run)
        suite = StartSuite(run_uuid, ['suite'])
        suite_temp = self.client.start_suite(suite)[0]
        test = StartTest(run_uuid, suite_temp, 'tname', datetime.now(timezone.utc), TestType.TEST)
        test_temp = self.client.start_test(test)
        self.assertTrue(self.client._OrangebeardClient__call_events[test_temp].is_set())
        finish = FinishTest(run_uuid, TestStatus.PASSED, datetime.now(timezone.utc))
        self.client.finish_test(test_temp, finish)
        loop = self.client._OrangebeardClient__event_loop
        loop.run_until_complete(asyncio.sleep(0))
        # ensure finish event set
        self.assertEqual(len(self.client._OrangebeardClient__call_events), 4)

    def test_start_step_and_finish_step_and_log_and_attachment(self):
        def fake_request(method, uri, data=None, headers=None):
            return DummyResponse(text='attach')
        self.client._OrangebeardClient__client.request = fake_request
        self.client._OrangebeardClient__make_api_request = AsyncMock(side_effect=[str(uuid.uuid4()), [{'suiteUUID': 'real-suite'}], 'real-test', 'real-step', 'real-log'])
        start_run = StartTestRun('set', datetime.now(timezone.utc), 'desc')
        run_uuid = self.client.start_test_run(start_run)
        suite = StartSuite(run_uuid, ['suite'])
        suite_temp = self.client.start_suite(suite)[0]
        test = StartTest(run_uuid, suite_temp, 'tname', datetime.now(timezone.utc), TestType.TEST)
        test_temp = self.client.start_test(test)
        step = StartStep(run_uuid, test_temp, 'step', datetime.now(timezone.utc))
        step_temp = self.client.start_step(step)
        self.assertTrue(self.client._OrangebeardClient__call_events[step_temp].is_set())
        log = Log(run_uuid, test_temp, 'msg', LogLevel.INFO, LogFormat.PLAIN_TEXT, None, datetime.now(timezone.utc))
        log_temp = self.client.log(log)
        self.client._OrangebeardClient__event_loop.run_until_complete(asyncio.sleep(0))
        self.assertEqual(self.client._OrangebeardClient__uuid_mapping[log_temp], 'real-log')
        meta = AttachmentMetaData(run_uuid, test_temp, log_temp)
        attach = Attachment(AttachmentFile('f.txt', b'data'), meta)
        self.client.send_attachment(attach)
        self.client._OrangebeardClient__event_loop.run_until_complete(asyncio.sleep(0))
        # after attachment event set
        self.assertTrue(any(ev.is_set() for ev in self.client._OrangebeardClient__call_events.values()))

if __name__ == '__main__':
    unittest.main()
