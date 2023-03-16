from enum import Enum


class TestType(str, Enum):
    TEST = "TEST"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
