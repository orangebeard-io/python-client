import pytest

from orangebeard.OrangebeardClient import OrangebeardClient
from tests.fake_server import FakeOrangebeardServer

TOKEN = '11111111-1111-1111-1111-111111111111'


@pytest.fixture
def server():
    srv = FakeOrangebeardServer().start()
    yield srv
    srv.stop()


@pytest.fixture
def make_client(server):
    clients = []

    def factory(**kwargs):
        client = OrangebeardClient(endpoint=server.url, access_token=TOKEN, project_name='proj', **kwargs)
        clients.append(client)
        return client

    yield factory
    for c in clients:
        if hasattr(c, 'close'):
            c.close()
