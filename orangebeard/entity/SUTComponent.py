from orangebeard.entity.Serializable import Serializable


class SUTComponent(Serializable):
    def __init__(self, componentId, componentName, version, status, createdDateTime, updatedDateTime):
        self.componentId = componentId
        self.componentName = componentName
        self.version = version
        self.status = status
        self.createDateTime = createdDateTime.strftime("%Y-%m-%d %H:%M:%S%z")
        self.updateDateTime = updatedDateTime.strftime("%Y-%m-%d %H:%M:%S%z")
