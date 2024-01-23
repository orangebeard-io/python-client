from datetime import datetime
from typing import List
from uuid import UUID
from orangebeard.entity.Attribute import Attribute
from orangebeard.entity.Serializable import Serializable
from orangebeard.entity.TestType import TestType


class StartTest(Serializable):
    def __init__(
        self,
        testRunUUID: UUID,
        suiteUUID: UUID,
        testName: str,
        startTime: datetime,
        testType: TestType,
        decription: str = None,
        attributes: List[Attribute] = None,
    ):
        self.testRunUUID = testRunUUID
        self.suiteUUID = suiteUUID
        self.testName = testName
        self.testType = testType
        self.description = decription
        self.attributes = attributes
        self.startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S%z")
