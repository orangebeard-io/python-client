from orangebeard.entity.Serializable import Serializable


class FinishStep(Serializable):
    def __init__(self, testRunUUID, status, endTime):
        self.testRunUUID = testRunUUID
        self.status = status
        self.endTime = endTime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
