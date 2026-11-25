import asyncio
import json
import subprocess
import sys
import textwrap
import threading
import time
from datetime import datetime

from orangebeard.entity.Attachment import Attachment, AttachmentFile, AttachmentMetaData
from orangebeard.entity.FinishStep import FinishStep
from orangebeard.entity.FinishTest import FinishTest
from orangebeard.entity.FinishTestRun import FinishTestRun
from orangebeard.entity.Log import Log
from orangebeard.entity.LogFormat import LogFormat
from orangebeard.entity.LogLevel import LogLevel
from orangebeard.entity.StartStep import StartStep
from orangebeard.entity.StartSuite import StartSuite
from orangebeard.entity.StartTest import StartTest
from orangebeard.entity.StartTestRun import StartTestRun
from orangebeard.entity.TestStatus import TestStatus as Status
from orangebeard.entity.TestType import TestType as Kind
from tests.conftest import TOKEN
from tests.fake_server import FakeOrangebeardServer

NOW = datetime.now().astimezone()


def run_rf_like_sequence(client, with_attachment=True):
    """The call sequence the Robot Framework listener performs (public API only)."""
    run = client.start_test_run(StartTestRun('set', NOW, 'desc'))
    suites = client.start_suite(StartSuite(run, ['Parent', 'Child']))
    test = client.start_test(StartTest(run, suites[-1], 'a test', NOW, Kind.TEST))
    step = client.start_step(StartStep(run, test, 'a step', NOW))
    log = client.log(Log(run, test, 'hello', LogLevel.INFO, LogFormat.PLAIN_TEXT, step, NOW))
    if with_attachment:
        client.send_attachment(Attachment(AttachmentFile('a.txt', b'data'), AttachmentMetaData(run, test, log, step)))
    client.finish_step(step, FinishStep(run, Status.PASSED, NOW))
    client.finish_test(test, FinishTest(run, Status.PASSED, NOW))
    client.finish_test_run(run, FinishTestRun(NOW))
    return run


def test_dependent_calls_carry_real_uuids(server, make_client):
    client = make_client()
    run_rf_like_sequence(client)

    suite_req = server.of('/suite/start')[0]['body']
    paths = server.paths()
    assert paths[0] == ('POST', 'test-run/start')
    assert ('POST', 'suite/start') in paths and ('POST', 'test/start') in paths and ('POST', 'step/start') in paths
    assert paths[-1][0] == 'PUT' and paths[-1][1].startswith('test-run/finish/')

    # the finish url must carry the real (server issued) run uuid, not the client side temp uuid
    run_uuid = paths[-1][1].rsplit('/', 1)[1]
    assert suite_req['testRunUUID'] == run_uuid
    test_req = server.of('/test/start')[0]['body']
    assert test_req['testRunUUID'] == run_uuid
    assert test_req['suiteUUID'] and test_req['suiteUUID'] != run_uuid
    log_req = server.of('/log')[0]['body']
    assert log_req['testUUID'] and log_req['stepUUID'] and log_req['testRunUUID'] == run_uuid
    attachment = server.of('/attachment')[0]
    assert attachment['method'] == 'POST'


def test_finish_test_run_flushes_pending_fire_and_forget_calls():
    srv = FakeOrangebeardServer(delay=0.05).start()
    try:
        from orangebeard.OrangebeardClient import OrangebeardClient
        client = OrangebeardClient(endpoint=srv.url, access_token=TOKEN, project_name='proj')
        run_rf_like_sequence(client)
        names = [p[1] for p in srv.paths()]
        assert names.count('log') == 1
        assert any(n.startswith('step/finish/') for n in names)
        assert any(n.startswith('test/finish/') for n in names)
        assert names[-1].startswith('test-run/finish/')
        client.close()
    finally:
        srv.stop()


def test_start_calls_do_not_block_the_caller():
    srv = FakeOrangebeardServer(delay=0.3).start()
    try:
        from orangebeard.OrangebeardClient import OrangebeardClient
        client = OrangebeardClient(endpoint=srv.url, access_token=TOKEN, project_name='proj')
        began = time.monotonic()
        run = client.start_test_run(StartTestRun('set', NOW, 'desc'))
        suites = client.start_suite(StartSuite(run, ['S']))
        test = client.start_test(StartTest(run, suites[0], 't', NOW, Kind.TEST))
        client.start_step(StartStep(run, test, 's', NOW))
        assert time.monotonic() - began < 0.25  # four sequential 0.3s calls would take >1.2s
        client.finish_test_run(run, FinishTestRun(NOW))
        assert len(srv.of('/step/start')) == 1
        client.close()
    finally:
        srv.stop()


def test_works_while_an_event_loop_is_running_in_the_calling_thread(server, make_client):
    client = make_client()

    async def inside_running_loop():
        run_rf_like_sequence(client)

    asyncio.run(inside_running_loop())
    assert server.paths()[-1][1].startswith('test-run/finish/')


def test_constructing_a_client_does_not_install_an_event_loop_in_the_calling_thread(server):
    from orangebeard.OrangebeardClient import OrangebeardClient
    outcome = {}

    def work():
        client = OrangebeardClient(endpoint=server.url, access_token=TOKEN, project_name='proj')
        try:
            asyncio.get_event_loop()
            outcome['loop'] = True
        except RuntimeError:
            outcome['loop'] = False
        client.close()

    t = threading.Thread(target=work)
    t.start()
    t.join(10)
    assert outcome['loop'] is False


def test_log_batch_is_sent_as_one_batch_request(server, make_client):
    client = make_client()
    run = client.start_test_run(StartTestRun('set', NOW, 'desc'))
    suites = client.start_suite(StartSuite(run, ['S']))
    test = client.start_test(StartTest(run, suites[0], 't', NOW, Kind.TEST))
    for i in range(5):
        client.log_batch(Log(run, test, f'm{i}', LogLevel.INFO, LogFormat.PLAIN_TEXT, None, NOW))
    client.finish_test(test, FinishTest(run, Status.PASSED, NOW))
    client.finish_test_run(run, FinishTestRun(NOW))

    batches = server.of('/log/batch')
    assert len(batches) == 1
    entries = batches[0]['body']
    assert [e['message'] for e in entries] == [f'm{i}' for i in range(5)]
    assert all(e['testUUID'] and e['testRunUUID'] for e in entries)  # real uuids, not None
    assert server.of('/log') == []
    # the log batch lands before the test is finished
    names = [p[1] for p in server.paths()]
    assert names.index('log/batch') < next(i for i, n in enumerate(names) if n.startswith('test/finish/'))


def test_log_batch_flushes_when_the_buffer_is_full(server, make_client):
    client = make_client(log_batch_size=3)
    run = client.start_test_run(StartTestRun('set', NOW, 'desc'))
    suites = client.start_suite(StartSuite(run, ['S']))
    test = client.start_test(StartTest(run, suites[0], 't', NOW, Kind.TEST))
    for i in range(7):
        client.log_batch(Log(run, test, f'm{i}', LogLevel.INFO, LogFormat.PLAIN_TEXT, None, NOW))
    client.finish_test_run(run, FinishTestRun(NOW))
    sizes = [len(b['body']) for b in server.of('/log/batch')]
    assert sizes == [3, 3, 1]


def test_log_batch_flushes_on_interval(server, make_client):
    client = make_client(log_batch_interval=0.2)
    run = client.start_test_run(StartTestRun('set', NOW, 'desc'))
    suites = client.start_suite(StartSuite(run, ['S']))
    test = client.start_test(StartTest(run, suites[0], 't', NOW, Kind.TEST))
    client.log_batch(Log(run, test, 'lonely', LogLevel.INFO, LogFormat.PLAIN_TEXT, None, NOW))
    deadline = time.monotonic() + 3
    while not server.of('/log/batch') and time.monotonic() < deadline:
        time.sleep(0.05)
    assert len(server.of('/log/batch')) == 1


def test_external_run_lifecycle_does_not_finish_the_run(server):
    from orangebeard.OrangebeardClient import OrangebeardClient
    from orangebeard.entity.OrangebeardParameters import OrangebeardParameters
    import uuid
    run = uuid.uuid4()
    cfg = OrangebeardParameters(token=TOKEN, endpoint=server.url, project='proj', testrun_uuid=run)
    client = OrangebeardClient(orangebeard_config=cfg)
    suites = client.start_suite(StartSuite(run, ['S']))
    assert suites
    client.finish_test_run(run, FinishTestRun(NOW))
    assert not any(p[1].startswith('test-run/finish') for p in server.paths())
    client.close()


def test_unflushed_batch_logs_are_sent_at_interpreter_exit(server):
    script = textwrap.dedent(f"""
        from datetime import datetime
        from orangebeard.OrangebeardClient import OrangebeardClient
        from orangebeard.entity.Log import Log
        from orangebeard.entity.StartSuite import StartSuite
        from orangebeard.entity.StartTest import StartTest
        from orangebeard.entity.StartTestRun import StartTestRun
        from orangebeard.entity.TestType import TestType
        now = datetime.now().astimezone()
        c = OrangebeardClient(endpoint={server.url!r}, access_token={TOKEN!r}, project_name='proj')
        run = c.start_test_run(StartTestRun('set', now, 'd'))
        s = c.start_suite(StartSuite(run, ['S']))
        t = c.start_test(StartTest(run, s[0], 't', now, TestType.TEST))
        c.log_batch(Log(run, t, 'left behind', 'INFO', 'PLAIN_TEXT', None, now))
    """)
    subprocess.run([sys.executable, '-c', script], check=True, timeout=60)
    batches = server.of('/log/batch')
    assert len(batches) == 1 and batches[0]['body'][0]['message'] == 'left behind'


def test_public_contract_is_unchanged(make_client):
    client = make_client()
    assert isinstance(client.call_events, dict)
    assert isinstance(client.uuid_mapping, dict)
    for name in ('start_test_run', 'start_announced_test_run', 'finish_test_run', 'start_suite', 'start_test',
                 'finish_test', 'start_step', 'finish_step', 'log', 'send_attachment'):
        assert callable(getattr(client, name))
