import asyncio
import uuid
from asyncio.locks import Event
from types import MappingProxyType

import aiohttp

from uuid import UUID

from aiohttp import ContentTypeError, ClientError

from orangebeard.config import AutoConfig
from orangebeard.entity.Attachment import Attachment
from orangebeard.entity.FinishStep import FinishStep
from orangebeard.entity.FinishTest import FinishTest
from orangebeard.entity.FinishTestRun import FinishTestRun
from orangebeard.entity.Log import Log
from orangebeard.entity.OrangebeardParameters import OrangebeardParameters
from orangebeard.entity.Serializable import Serializable
from orangebeard.entity.StartStep import StartStep
from orangebeard.entity.StartSuite import StartSuite
from orangebeard.entity.StartTest import StartTest
from orangebeard.entity.StartTestRun import StartTestRun
from orangebeard.entity.Suite import Suite


class OrangebeardClient:
    """
        OrangebeardClient class for interacting with the Orangebeard API.

        Args:
            endpoint (str): The Orangebeard API endpoint.
            access_token (UUID): The access token for authentication.
            project_name (str): The name of the Orangebeard project.

        Attributes:
            __endpoint (str): The Orangebeard API endpoint.
            __access_token (UUID): The access token for authentication.
            __project_name (str): The name of the Orangebeard project.
            __connection_with_orangebeard_is_valid (bool): Flag indicating whether the connection with
            Orangebeard is valid.
            __uuid_mapping (dict): Mapping of temporary UUIDs to actual UUIDs.
            __call_events (dict): Mapping of UUIDs to asyncio.Event objects.
            __client (aiohttp.ClientSession): A client session for making API requests.
        """

    def __init__(
            self,
            endpoint: str = None,
            access_token: UUID = None,
            project_name: str = None,
            orangebeard_config: OrangebeardParameters = None
    ) -> None:
        """
            Initialize the OrangebeardClient.

            Args:
                endpoint (str): The Orangebeard API endpoint.
                access_token (UUID): The access token for authentication.
                project_name (str): The name of the Orangebeard project.
            """

        if endpoint is None or access_token is None or project_name is None:
            if orangebeard_config is not None:
                config = AutoConfig.update_config_parameters_from_env(orangebeard_config)
            else:
                config = AutoConfig.config

            endpoint = config.endpoint
            access_token = config.token
            project_name = config.project

        self.__endpoint = endpoint
        self.__access_token = access_token
        self.__project_name = project_name
        self.__connection_with_orangebeard_is_valid: bool = True

        self.__uuid_mapping = {}
        self.__call_events = {}
        self.__event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__event_loop)

        self.__client = aiohttp.ClientSession(
            base_url=self.__endpoint,
            headers={
                "Authorization": f"Bearer {str(self.__access_token)}",
                "Content-Type": "application/json",
            },
            raise_for_status=True)

    def start_test_run(self, start_test_run: StartTestRun) -> UUID:
        """
        Start a new test run.

        Args:
            start_test_run (StartTestRun): The StartTestRun object containing information about the test run.

        Returns:
            UUID: The UUID associated with the started test run.
        """
        temp_uuid = uuid.uuid4()
        start_test_run_event = asyncio.Event()

        self.__call_events[temp_uuid] = start_test_run_event

        self.__event_loop.run_until_complete(self.__exec_start_test_run(start_test_run, temp_uuid))
        return temp_uuid

    def start_announced_test_run(self, test_run_uuid: UUID) -> None:
        """
        Start an announced test run.

        Args:
            test_run_uuid (UUID): The UUID of the test run to be started.
        """
        start_test_run_event = asyncio.Event()
        self.__call_events[test_run_uuid] = start_test_run_event
        self.__event_loop.run_until_complete(self.__exec_start_announced_test_run(test_run_uuid))

    def finish_test_run(self, test_run_uuid: UUID, finish_test_run: FinishTestRun) -> None:
        """
        Wait for all events to finish and then finish the test run.

        Args:
            test_run_uuid (UUID): The UUID of the test run to be finished.
            finish_test_run (FinishTestRun): The FinishTestRun object containing information about finishing the
            test run.
        """
        self.__event_loop.run_until_complete(
            self.__exec_finish_test_run(test_run_uuid, finish_test_run))

    def start_suite(self, start_suite: StartSuite) -> list[UUID]:
        """
        Start a suite and return a list of UUIDs associated with the started suites.

        Args:
            start_suite (StartSuite): The StartSuite object containing information about the suite.

        Returns:
            list[UUID]: List of UUIDs associated with the started suites.
        """
        start_suite_event = asyncio.Event()
        temp_uuids = [uuid.uuid4() for _ in start_suite.suiteNames]
        for temp_uuid in temp_uuids:
            self.__call_events[temp_uuid] = start_suite_event

        parent_event_uuid: UUID = start_suite.testRunUUID if start_suite.parentSuiteUUID is None \
            else start_suite.parentSuiteUUID
        parent_event = self.__call_events[parent_event_uuid]

        self.__event_loop.run_until_complete(self.__exec_start_suite(start_suite, temp_uuids, parent_event))
        return temp_uuids

    def start_test(self, start_test: StartTest) -> UUID:
        """
        Start a test.

        Args:
            start_test (StartTest): The StartTest object containing information about the test.

        Returns:
            UUID: The UUID associated with the started test.
        """
        start_test_event = asyncio.Event()
        temp_uuid = uuid.uuid4()
        self.__call_events[temp_uuid] = start_test_event

        parent_event = self.__call_events[start_test.suiteUUID]
        self.__event_loop.run_until_complete(self.__exec_start_test(start_test, temp_uuid, parent_event))
        return temp_uuid

    def finish_test(self, test_uuid: UUID, finish_test: FinishTest) -> None:
        """
        Finish a test.

        Args:
            test_uuid (UUID): The UUID of the test to be finished.
            finish_test (FinishTest): The FinishTest object containing information about finishing the test.
        """
        finish_test_event = asyncio.Event()
        temp_uuid = uuid.uuid4()
        self.__call_events[temp_uuid] = finish_test_event

        parent_event = self.__call_events[test_uuid]
        asyncio.ensure_future(self.__exec_finish_test(test_uuid, finish_test, temp_uuid, parent_event))

    def start_step(self, start_step: StartStep) -> UUID:
        """
        Start a step.

        Args:
            start_step (StartStep): The StartStep object containing information about the step.

        Returns:
            UUID: The UUID associated with the started step.
        """
        start_step_event = asyncio.Event()
        temp_uuid = uuid.uuid4()
        self.__call_events[temp_uuid] = start_step_event

        parent_event_uuid = start_step.testUUID if start_step.parentStepUUID is None \
            else start_step.parentStepUUID

        parent_event = self.__call_events[parent_event_uuid]

        self.__event_loop.run_until_complete(self.__exec_start_step(start_step, temp_uuid, parent_event))
        return temp_uuid

    def finish_step(self, step_uuid: UUID, finish_step: FinishStep) -> None:
        """
        Finish a step.

        Args:
            step_uuid (UUID): The UUID of the step to be finished.
            finish_step (FinishStep): The FinishStep object containing information about finishing the step.
        """
        finish_step_event = asyncio.Event()
        temp_uuid = uuid.uuid4()
        self.__call_events[temp_uuid] = finish_step_event

        parent_event = self.__call_events[step_uuid]
        asyncio.ensure_future(self.__exec_finish_step(step_uuid, finish_step, temp_uuid, parent_event))

    def log(self, log: Log) -> UUID:
        """
        Send a log.

        Args:
            log (Log): The Log object containing information to store.

        Returns:
            UUID: The UUID associated with the log.
        """
        log_event = asyncio.Event()
        temp_uuid = uuid.uuid4()
        self.__call_events[temp_uuid] = log_event

        parent_event_uuid = log.testUUID if log.stepUUID is None \
            else log.stepUUID
        parent_event = self.__call_events[parent_event_uuid]

        asyncio.ensure_future(self.__exec_log(log, temp_uuid, parent_event))
        return temp_uuid

    def send_attachment(self, attachment: Attachment) -> UUID:
        """
        Send an attachment. (to attach to a log)

        Args:
            attachment (Attachment): The Attachment object containing information about the attachment.

        Returns:
            UUID: The UUID associated with the attachment that was sent.
        """
        attachment_event = asyncio.Event()
        temp_uuid = uuid.uuid4()
        self.__call_events[temp_uuid] = attachment_event

        parent_event = self.__call_events[attachment.AttachmentMetaData.logUUID]
        asyncio.ensure_future(self.__exec_send_attachment(attachment, temp_uuid, parent_event))
        return temp_uuid

    async def __make_api_request(self, method: str, uri: str, data: Serializable = None, retry_count: int = 4):
        for attempt in range(retry_count):
            if self.__connection_with_orangebeard_is_valid:
                try:
                    async with (self.__client.request(method, uri, data=data.to_json() if data is not None else None)
                                as response):
                        try:
                            return await response.json()
                        except ContentTypeError:
                            return None
                except ClientError:
                    await asyncio.sleep(2 ** (attempt + 1))
            else:
                break
        else:
            self.__connection_with_orangebeard_is_valid = False
            raise ConnectionError(f'Failed to communicate with Orangebeard after {retry_count} attempts')

    async def __exec_start_test_run(self, start_test_run: StartTestRun, temp_uuid: UUID) -> None:
        response = await self.__make_api_request(
            'POST',
            f'/listener/v3/{self.__project_name}/test-run/start',
            start_test_run
        )
        actual_uuid = response if response else None
        self.__uuid_mapping[temp_uuid] = actual_uuid
        self.__call_events[temp_uuid].set()

    async def __exec_start_announced_test_run(self, test_run_uuid: UUID) -> None:
        await self.__make_api_request(
            'PUT',
            f'/listener/v3/{self.__project_name}/test-run/start/{test_run_uuid}'
        )
        self.__uuid_mapping[test_run_uuid] = test_run_uuid
        self.__call_events[test_run_uuid].set()

    async def __exec_finish_test_run(self, test_run_uuid: UUID, finish_test_run: FinishTestRun) -> None:
        print(f'Waiting for {len(self.__call_events.values()) + 1} Orangebeard events to finish...')

        for event in self.__call_events.values():
            await event.wait()

        real_test_run_uuid = self.__uuid_mapping[test_run_uuid]
        await self.__make_api_request(
            'PUT',
            f'/listener/v3/{self.__project_name}/test-run/finish/{real_test_run_uuid}',
            finish_test_run
        )
        print('Done. Test run finished!')
        await self.__client.close()

    async def __exec_start_suite(self, start_suite: StartSuite, suite_temp_ids: list[UUID],
                                 parent_event: Event) -> None:
        await parent_event.wait()

        start_suite.testRunUUID = self.__uuid_mapping[start_suite.testRunUUID]
        if start_suite.parentSuiteUUID is not None:
            start_suite.parentSuiteUUID = self.__uuid_mapping[start_suite.parentSuiteUUID]

        suites: list[Suite] = await self.__make_api_request(
            'POST',
            f'/listener/v3/{self.__project_name}/suite/start',
            start_suite
        )

        actual_uuids = [suite['suiteUUID'] for suite in suites]
        for i, temp_uuid in enumerate(suite_temp_ids):
            self.__uuid_mapping[temp_uuid] = actual_uuids[i]
            self.__call_events[temp_uuid].set()

    async def __exec_start_test(self, start_test: StartTest, temp_uuid: UUID, parent_event: Event) -> None:
        await parent_event.wait()
        start_test.testRunUUID = self.__uuid_mapping[start_test.testRunUUID]
        start_test.suiteUUID = self.__uuid_mapping[start_test.suiteUUID]

        response = await self.__make_api_request(
            'POST',
            f'/listener/v3/{self.__project_name}/test/start',
            start_test
        )
        actual_uuid = response if response else None
        self.__uuid_mapping[temp_uuid] = actual_uuid
        self.__call_events[temp_uuid].set()

    async def __exec_finish_test(self, test_uuid: UUID, finish_test: FinishTest, temp_uuid: UUID,
                                 parent_event: Event) -> None:
        await parent_event.wait()
        test_uuid = self.__uuid_mapping[test_uuid]
        finish_test.testRunUUID = self.__uuid_mapping[finish_test.testRunUUID]

        await self.__make_api_request(
            'PUT',
            f'/listener/v3/{self.__project_name}/test/finish/{test_uuid}',
            finish_test
        )
        self.__call_events[temp_uuid].set()

    async def __exec_start_step(self, start_step: StartStep, temp_uuid: UUID, parent_event: Event) -> None:
        await parent_event.wait()
        start_step.testRunUUID = self.__uuid_mapping[start_step.testRunUUID]
        start_step.testUUID = self.__uuid_mapping[start_step.testUUID]
        if start_step.parentStepUUID is not None:
            start_step.parentStepUUID = self.__uuid_mapping[start_step.parentStepUUID]

        response = await self.__make_api_request(
            'POST',
            f'/listener/v3/{self.__project_name}/step/start',
            start_step
        )

        actual_uuid = response if response else None
        self.__uuid_mapping[temp_uuid] = actual_uuid
        self.__call_events[temp_uuid].set()

    async def __exec_finish_step(self, step_uuid: UUID, finish_step: FinishStep, temp_uuid: UUID,
                                 parent_event: Event) -> None:
        await parent_event.wait()
        step_uuid = self.__uuid_mapping[step_uuid]
        finish_step.testRunUUID = self.__uuid_mapping[finish_step.testRunUUID]

        await self.__make_api_request(
            'PUT',
            f'/listener/v3/{self.__project_name}/step/finish/{step_uuid}',
            finish_step
        )
        self.__call_events[temp_uuid].set()

    async def __exec_log(self, log: Log, temp_uuid: UUID, parent_event: Event) -> None:
        await parent_event.wait()
        if log.message.strip() == '':
            log.message = '_empty_'
        log.testRunUUID = self.__uuid_mapping[log.testRunUUID]
        log.testUUID = self.__uuid_mapping[log.testUUID]
        log.stepUUID = self.__uuid_mapping[log.stepUUID] if log.stepUUID is not None else None

        response = await self.__make_api_request(
            'POST',
            f'/listener/v3/{self.__project_name}/log',
            log
        )

        actual_uuid = response if response else None
        self.__uuid_mapping[temp_uuid] = actual_uuid
        self.__call_events[temp_uuid].set()

    async def __exec_send_attachment(self, attachment: Attachment, temp_uuid: UUID, parent_event: Event) -> None:
        await parent_event.wait()
        attachment.AttachmentMetaData.testRunUUID = self.__uuid_mapping[attachment.AttachmentMetaData.testRunUUID]
        attachment.AttachmentMetaData.testUUID = self.__uuid_mapping[attachment.AttachmentMetaData.testUUID]
        if attachment.AttachmentMetaData.stepUUID is not None:
            attachment.AttachmentMetaData.stepUUID = self.__uuid_mapping[attachment.AttachmentMetaData.stepUUID]
        attachment.AttachmentMetaData.logUUID = self.__uuid_mapping[attachment.AttachmentMetaData.logUUID]

        if self.__connection_with_orangebeard_is_valid:
            boundary = f"boundary_{uuid.uuid4().hex}"
            multipart_message = aiohttp.MultipartWriter('form-data', boundary=boundary)

            multipart_message.append(
                attachment.AttachmentMetaData.to_json(),
                MappingProxyType({'Content-Disposition': 'form-data; name="json"', 'Content-Type': 'application/json'})
            )
            multipart_message.append(
                attachment.AttachmentFile.content,
                MappingProxyType({
                    'Content-Disposition': f'form-data; name="attachment"; filename="{attachment.AttachmentFile.name}"',
                    'Content-Type': attachment.AttachmentFile.contentType
                })
            )

            headers = {
                'Authorization': f'Bearer {str(self.__access_token)}',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }

            uri = f'/listener/v3/{self.__project_name}/attachment'

            async with self.__client.request('POST', uri, data=multipart_message, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_text = await response.text()
                    actual_uuid = response_text if response_text else None
                    self.__uuid_mapping[temp_uuid] = actual_uuid
                    self.__call_events[temp_uuid].set()
                else:
                    self.__connection_with_orangebeard_is_valid = False
                    raise ConnectionError(f'Failed to communicate with Orangebeard: {await response.text()}')
