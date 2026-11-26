import sys

import pytest

from orangebeard import Cli
from orangebeard.config import AutoConfig
from tests.conftest import TOKEN


RUN = '33333333-3333-3333-3333-333333333333'


@pytest.fixture
def run_cli(server, tmp_path, monkeypatch):
    """Run `orangebeard-cli` against the fake server, with the given ORANGEBEARD_* variables set."""
    for name in ('ENDPOINT', 'TOKEN', 'PROJECT', 'TESTSET', 'DESCRIPTION', 'ATTRIBUTES', 'REFERENCE_URL',
                 'TESTRUN_UUID'):
        monkeypatch.delenv(f'ORANGEBEARD_{name}', raising=False)
    (tmp_path / 'orangebeard.json').write_text('{"attributes": [{"key": "team", "value": "web"}]}')

    def run(*arguments, env=None):
        for name, value in (env or {}).items():
            monkeypatch.setenv(name, value)
        monkeypatch.setattr(AutoConfig, 'config', AutoConfig.get_config(str(tmp_path)))
        monkeypatch.setattr(sys, 'argv', ['orangebeard-cli', '-e', server.url, '-t', TOKEN, '-p', 'proj',
                                          *arguments])
        with pytest.raises(SystemExit) as exit_info:
            Cli.main()
        assert exit_info.value.code == 0

    return run


@pytest.fixture
def start_run(server, run_cli):
    """Run `orangebeard-cli -x start` and return the attributes the server received."""

    def run(*extra):
        run_cli('-x', 'start', '-s', 'nightly', *extra)
        return server.of('/test-run/start')[0]['body'].get('attributes')

    return run


def test_attributes_given_on_the_command_line_are_added_to_the_configured_ones(start_run):
    assert start_run('--attributes', 'smoke;env:ci') == [
        {'key': 'team', 'value': 'web'}, {'key': None, 'value': 'smoke'}, {'key': 'env', 'value': 'ci'}]


def test_the_configured_attributes_are_sent_without_the_option(start_run):
    assert start_run() == [{'key': 'team', 'value': 'web'}]


@pytest.mark.parametrize('env', [{}, {'ORANGEBEARD_TESTRUN_UUID': RUN}], ids=['plain', 'uuid exported'])
def test_finish_finishes_the_run(server, run_cli, env):
    # in a CI job the variable that the tests report with is typically still set when the run is finished
    run_cli('-x', 'finish', '-id', RUN, env=env)
    assert len(server.of(f'/test-run/finish/{RUN}')) == 1
