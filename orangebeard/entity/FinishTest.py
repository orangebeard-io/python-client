from datetime import datetime
from uuid import UUID

from orangebeard.entity.Serializable import Serializable


class FinishTest(Serializable):
    def __init__(self, testRunUUID: UUID, status, endTime):
        self.testRunUUID = str(testRunUUID)
        self.status = status
        self.endTime = endTime.strftime("%Y-%m-%dT%H:%M:%S%z")
