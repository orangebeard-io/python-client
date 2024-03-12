from orangebeard.entity.Serializable import Serializable


class FinishTestRun(Serializable):
    def __init__(self, endTime):
        self.endTime = endTime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
