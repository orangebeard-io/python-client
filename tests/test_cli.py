import sys

import pytest

from orangebeard import Cli
from orangebeard.config import AutoConfig
from tests.conftest import TOKEN


@pytest.fixture
def start_run(server, tmp_path, monkeypatch):
    """Run `orangebeard-cli -x start` and return the attributes the server received."""
    for name in ('ENDPOINT', 'TOKEN', 'PROJECT', 'TESTSET', 'DESCRIPTION', 'ATTRIBUTES', 'REFERENCE_URL',
                 'TESTRUN_UUID'):
        monkeypatch.delenv(f'ORANGEBEARD_{name}', raising=False)
    (tmp_path / 'orangebeard.json').write_text('{"attributes": [{"key": "team", "value": "web"}]}')
    monkeypatch.setattr(AutoConfig, 'config', AutoConfig.get_config(str(tmp_path)))

    def run(*extra):
        monkeypatch.setattr(sys, 'argv', ['orangebeard-cli', '-x', 'start', '-e', server.url, '-t', TOKEN,
                                          '-p', 'proj', '-s', 'nightly', *extra])
        with pytest.raises(SystemExit) as exit_info:
            Cli.main()
        assert exit_info.value.code == 0
        return server.of('/test-run/start')[0]['body'].get('attributes')

    return run


def test_attributes_given_on_the_command_line_are_added_to_the_configured_ones(start_run):
    assert start_run('--attributes', 'smoke;env:ci') == [
        {'key': 'team', 'value': 'web'}, {'key': None, 'value': 'smoke'}, {'key': 'env', 'value': 'ci'}]


def test_the_configured_attributes_are_sent_without_the_option(start_run):
    assert start_run() == [{'key': 'team', 'value': 'web'}]
