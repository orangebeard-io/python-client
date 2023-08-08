from typing import List
from orangebeard.entity.Attribute import Attribute
from orangebeard.entity.Serializable import Serializable


class StartTestRun(Serializable):
    def __init__(
        self,
        testSetName,
        startTime,
        description,
        attributes: List[Attribute],
        changedComponents,
    ):
        self.testSetName = testSetName
        self.description = description
        self.startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S%z")
        self.attributes = attributes
        self.changedComponents = changedComponents
