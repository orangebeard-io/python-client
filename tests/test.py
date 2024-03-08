import re
from pytz import reference
import uuid

from orangebeard.OrangebeardClient import OrangebeardClient
from orangebeard.entity.Attachment import AttachmentFile, AttachmentMetaData, Attachment
from orangebeard.entity.FinishStep import FinishStep
from orangebeard.entity.FinishTest import FinishTest
from orangebeard.entity.FinishTestRun import FinishTestRun
from orangebeard.entity.Log import Log
from orangebeard.entity.LogFormat import LogFormat
from orangebeard.entity.StartStep import StartStep
from orangebeard.entity.StartSuite import StartSuite
from orangebeard.entity.StartTest import StartTest
from orangebeard.entity.StartTestRun import StartTestRun
from orangebeard.entity.TestStatus import TestStatus
from orangebeard.entity.TestType import TestType
from orangebeard.entity.LogLevel import LogLevel

from datetime import datetime

endpoint = 'https://praegus.orangebeard.app'
token = 'f11a09e7-cb14-4e02-953d-03ad1a49bad1'
project = 'tom_personal'

tz = reference.LocalTimezone()


def pad_suite_name(suite_name) -> str:
    if len(suite_name) < 3:
        return suite_name + "  "
    return suite_name


def parse_logfile(filename):
    result = []
    current_item = ""

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()

            # Use regular expression to match the pattern
            match = re.match(r'\[([a-zA-Z]+)]: (.*)', line)

            if match:
                # If a pattern match is found, add the current item to the result list
                if current_item:
                    result.append(current_item)
                # Start a new item with the matched pattern and the following lines
                current_item = f"[{match.group(1)}]: {match.group(2)}\n"
            else:
                # If no match, add the line to the current item
                current_item += line + "\n"

    # Add the last item to the result list
    if current_item:
        result.append(current_item)

    return result


def main():
    filename = "./test_log.txt"
    log_list = parse_logfile(filename)

    client = OrangebeardClient(endpoint, token, project)

    start_time = datetime.now(tz)
    print('Start: {0}', start_time.timestamp())
    test_run_uuid = client.start_test_run(StartTestRun('Python Client Test Set', start_time, 'A description'))
    print('Started run: {0}\n'.format(test_run_uuid))

    suite_key = 'UI.TestSuite.Banaan'
    suite_names = list(map(pad_suite_name, suite_key.split(".")))
    suite_uuids = client.start_suite(StartSuite(test_run_uuid, suite_names))
    print('\tStarted suite: {0}\n'.format(suite_uuids))

    test_uuid = client.start_test(
        StartTest(test_run_uuid, suite_uuids[len(suite_uuids)-1], "Salarisverwerking data iteration #2", start_time, TestType.TEST,
                  'A test description'))
    print('\tStarted test: {0}\n'.format(test_uuid))
    step_uuid = None
    level = None
    log_uuid = None

    for item in log_list:
        print(item)
        if item.startswith('[Step]'):
            print(item)
            if step_uuid is not None:
                print(item)
                step_status = TestStatus.FAILED if level == LogLevel.ERROR else TestStatus.PASSED
                client.finish_step(step_uuid, FinishStep(test_run_uuid, step_status, datetime.now(tz)))
            step_uuid = client.start_step(StartStep(test_run_uuid, test_uuid, item, datetime.now(tz)))
            print('Start step: ' + item)
        else:
            level = LogLevel.ERROR if item.startswith('[Module]: Failed') or item.startswith(
                '[Screenshot]: Failed') else LogLevel.INFO
            log_uuid = client.log(
                Log(test_run_uuid, test_uuid, item, level, LogFormat.PLAIN_TEXT, step_uuid, datetime.now(tz)))

    attachment_file = AttachmentFile('logo.svg', open('../.github/logo.svg', 'rb').read())
    attachment_meta = AttachmentMetaData(test_run_uuid, test_uuid, log_uuid, step_uuid)

    client.send_attachment(Attachment(attachment_file, attachment_meta))

    client.finish_step(step_uuid, FinishStep(test_run_uuid, TestStatus.FAILED, datetime.now(tz)))

    client.finish_test(test_uuid, FinishTest(test_run_uuid, TestStatus.FAILED, datetime.now(tz)))

    client.finish_test_run(test_run_uuid, FinishTestRun(datetime.now(tz)))
    end_time = datetime.now(tz)
    print('Finish: {0}', end_time.timestamp())

    elapsed = end_time - start_time
    print('Elapsed: {0}', elapsed)


main()
