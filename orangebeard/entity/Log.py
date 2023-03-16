from orangebeard.entity.Serializable import Serializable


class Log(Serializable):
    def __init__(
        self, testRunUUID, testUUID, message, logLevel, logFormat, stepUUID, logTime
    ):
        self.testRunUUID = str(testRunUUID)
        self.testUUID = str(testUUID)
        self.stepUUID = str(stepUUID) if stepUUID else None
        self.logTime = logTime.strftime("%Y-%m-%dT%H:%M:%S%z")
        self.message = message
        self.logLevel = logLevel
        self.logFormat = logFormat
