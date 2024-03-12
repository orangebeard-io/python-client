from uuid import UUID

from orangebeard.entity.Attribute import Attribute
from orangebeard.entity.Serializable import Serializable


class StartSuite(Serializable):
    def __init__(
            self,
            testRunUUID: UUID,
            suiteNames: list[str],
            parentSuiteUUID: UUID = None,
            description: str = None,
            attributes: list[Attribute] = None,
    ):
        self.testRunUUID = testRunUUID
        self.parentSuiteUUID = parentSuiteUUID if parentSuiteUUID else None
        self.description = description
        self.attributes = attributes
        self.suiteNames = suiteNames
