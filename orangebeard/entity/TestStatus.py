from enum import Enum


class TestStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    STOPPED = "STOPPED"
    TIMED_OUT = "TIMED_OUT"
