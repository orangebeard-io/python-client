from datetime import datetime
import mimetypes
from uuid import UUID
from pytz import reference


from orangebeard.entity.Serializable import Serializable

tz = reference.LocalTimezone()


class AttachmentFile:
    def __init__(self, name, content, contentType=None):
        self.name = name
        self.content: bytes = content
        self.contentType = contentType or mimetypes.guess_type(name)


class AttachmentMetaData(Serializable):
    def __init__(
        self,
        testRunUUID: UUID,
        testUUID: UUID,
        logUUID: UUID,
        stepUUID: UUID=None, # type: ignore
        attachmentTime=datetime.now(tz),
    ):
        self.testRunUUID = str(testRunUUID)
        self.testUUID = str(testUUID)
        self.stepUUID = str(stepUUID) if stepUUID else None
        self.logUUID = str(logUUID)
        self.attachmentTime = attachmentTime.strftime("%Y-%m-%dT%H:%M:%S%z")
