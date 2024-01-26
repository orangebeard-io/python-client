from datetime import datetime
from uuid import UUID
from orangebeard.entity.Serializable import Serializable


class StartStep(Serializable):
    def __init__(
        self,
        testRunUUID: UUID,
        testUUID: UUID,
        stepName: str,
        startTime: datetime,
        parentStepUUID: UUID = None,
        description: str = None,
    ):
        self.testRunUUID = testRunUUID
        self.testUUID = testUUID
        self.parentStepUUID = parentStepUUID if parentStepUUID else None
        self.stepName = stepName
        self.description = description
        self.startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
