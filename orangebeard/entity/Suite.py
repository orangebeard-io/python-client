from uuid import UUID
from orangebeard.entity.Serializable import Serializable


class Suite(Serializable):
    def __init__(
        self,
        suiteUUID: UUID,
        parentUUID: UUID,
        localSuiteName: str,
        fullSuitePath: list[str],
    ):
        self.suiteUUID = str(suiteUUID)
        self.parentUUID = str(parentUUID) if parentUUID else None
        self.localSuiteName = localSuiteName
        self.fullSuitePath = fullSuitePath
