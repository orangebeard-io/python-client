from orangebeard.entity.Serializable import Serializable


class Log(Serializable):
    def __init__(
            self, testRunUUID, testUUID, message, logLevel, logFormat, stepUUID, logTime
    ):
        self.testRunUUID = testRunUUID
        self.testUUID = testUUID
        self.stepUUID = stepUUID if stepUUID else None
        self.logTime = logTime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        self.message = message
        self.logLevel = logLevel
        self.logFormat = logFormat
