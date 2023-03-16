from datetime import datetime

from orangebeard.entity.Serializable import Serializable


class FinishStep(Serializable):
    def __init__(self, testRunUUID, status, endTime):
        self.testRunUUID = str(testRunUUID)
        self.status = status
        self.endTime = endTime.strftime("%Y-%m-%dT%H:%M:%S%z")
