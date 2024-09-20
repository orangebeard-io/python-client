import argparse
import asyncio
import sys

from datetime import datetime

from orangebeard.OrangebeardClient import OrangebeardClient
from orangebeard.config import AutoConfig
from orangebeard.entity.FinishTestRun import FinishTestRun
from orangebeard.entity.StartTestRun import StartTestRun
from pytz import reference

tz = reference.LocalTimezone()


def main():
    config = AutoConfig.config

    parser = argparse.ArgumentParser(prog="Orangebeard CommandLine Utility",
                                     description="CLI to start or finish a test run")
    parser.add_argument('-e', '--endpoint', help="Your Orangebeard endpoint", default=config.endpoint)
    parser.add_argument('-t', '--accessToken', help="Your Orangebeard Access Token", default=config.token)
    parser.add_argument('-p', '--project', help="Orangebeard Project Name", default=config.project)
    parser.add_argument('-x', '--cmd', required=True, choices=['start', 'finish'], help="Command to execute")
    parser.add_argument('-s', '--testset', help="The testset name, required for start command", default=config.testset)
    parser.add_argument('-d', '--description', help="The test run description", default=config.description)
    parser.add_argument('-id', '--testRunUuid', help="The UUID of the test run to finish, required for finish",
                        default=None)

    args = parser.parse_args()

    config.endpoint = args.endpoint
    config.token = args.accessToken
    config.project = args.project
    config.test_set = args.testset
    config.description = args.description

    client = OrangebeardClient(orangebeard_config=config)

    if args.cmd == "start":
        temp_uuid = client.start_test_run(StartTestRun(config.testset, datetime.now(tz), config.description), True)
        asyncio.gather(client.call_events[temp_uuid].wait())
        print(client.uuid_mapping[temp_uuid])
        sys.exit(0)

    else:
        if args.cmd == "finish" and args.testRunUuid is not None:
            client.finish_test_run(args.testRunUuid, FinishTestRun(datetime.now(tz)), True)
            print('Orangebeard report Finished!')
            sys.exit(0)

    parser.print_help()
    sys.exit(1)


if __name__ == '__main__':
    main()
