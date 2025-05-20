import asyncio
import uuid
import unittest
from unittest.mock import AsyncMock, patch
from aiohttp import ClientError, ContentTypeError

from orangebeard.OrangebeardClient import OrangebeardClient

class DummyResponse:
    def __init__(self, json_data=None):
        self._json_data = json_data
        self.status = 200
    async def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass

class DummyClientSession:
    def __init__(self, responses):
        self.responses = responses
    def request(self, *args, **kwargs):
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp
    async def close(self):
        pass

class TestMakeApiRequest(unittest.IsolatedAsyncioTestCase):
    async def test_success(self):
        with patch('orangebeard.OrangebeardClient.aiohttp.ClientSession', lambda *a, **k: DummyClientSession([DummyResponse({'a':1})])):
            client = OrangebeardClient(endpoint='http://x', access_token=uuid.uuid4(), project_name='p')
            client._OrangebeardClient__client = DummyClientSession([DummyResponse({'a': 1})])
            result = await client._OrangebeardClient__make_api_request('GET', '/u')
            self.assertEqual(result, {'a': 1})

    async def test_content_type_error(self):
        with patch('orangebeard.OrangebeardClient.aiohttp.ClientSession', lambda *a, **k: DummyClientSession([DummyResponse(ContentTypeError(None, None))])):
            client = OrangebeardClient(endpoint='http://x', access_token=uuid.uuid4(), project_name='p')
            client._OrangebeardClient__client = DummyClientSession([DummyResponse(ContentTypeError(None, None))])
            result = await client._OrangebeardClient__make_api_request('GET', '/u')
            self.assertIsNone(result)

    async def test_retries_and_failure(self):
        with patch('orangebeard.OrangebeardClient.aiohttp.ClientSession', lambda *a, **k: DummyClientSession([ClientError(), ClientError()])):
            client = OrangebeardClient(endpoint='http://x', access_token=uuid.uuid4(), project_name='p')
            client._OrangebeardClient__client = DummyClientSession([ClientError(), ClientError()])
            async def sleep(_):
                return None
            asyncio_sleep = asyncio.sleep
            asyncio.sleep = sleep
            try:
                with self.assertRaises(ConnectionError):
                    await client._OrangebeardClient__make_api_request('GET', '/u', retry_count=2)
                self.assertFalse(client._OrangebeardClient__connection_with_orangebeard_is_valid)
            finally:
                asyncio.sleep = asyncio_sleep

if __name__ == '__main__':
    unittest.main()
