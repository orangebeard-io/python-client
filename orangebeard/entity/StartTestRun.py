from datetime import datetime
from typing import List
from orangebeard.entity.Attribute import Attribute
from orangebeard.entity.SUTComponent import SUTComponent
from orangebeard.entity.Serializable import Serializable


class StartTestRun(Serializable):
    def __init__(
        self,
        testSetName,
        startTime: datetime,
        description,
        attributes: List[Attribute] = None,
        sutComponents: List[SUTComponent] = None,
    ):
        self.testSetName = testSetName
        self.description = description
        self.startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        self.attributes = attributes
        self.sutComponents = sutComponents
