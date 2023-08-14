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
        testName,
        startTime,
        testType: TestType,
        decription,
        attributes: List[Attribute],
    ):
        self.testRunUUID = str(testRunUUID)
        self.suiteUUID = str(suiteUUID)
        self.testName = testName
        self.testType = testType
        self.decription = decription
        self.attributes = attributes
        self.startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S%z")
