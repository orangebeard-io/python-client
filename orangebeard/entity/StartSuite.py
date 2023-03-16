from uuid import UUID
from orangebeard.entity.Serializable import Serializable


class StartSuite(Serializable):
    def __init__(
        self,
        testRunUUID: UUID,
        suiteNames,
        parentSuiteUUID: UUID,
        description,
        attributes,
    ):
        self.testRunUUID = str(testRunUUID)
        self.parentSuiteUUID = str(parentSuiteUUID) if parentSuiteUUID else None
        self.description = description
        self.attributes = attributes
        self.suiteNames = suiteNames
