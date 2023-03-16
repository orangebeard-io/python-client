from uuid import UUID
from orangebeard.entity.Serializable import Serializable


class StartStep(Serializable):
    def __init__(
        self,
        testRunUUID: UUID,
        testUUID: UUID,
        parentStepUUID: UUID,
        stepName,
        startTime,
        description,
    ):
        self.testRunUUID = str(testRunUUID)
        self.testUUID = str(testUUID)
        self.parentStepUUID = str(parentStepUUID) if parentStepUUID else None
        self.stepName = stepName
        self.description = description
        self.startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S%z")
