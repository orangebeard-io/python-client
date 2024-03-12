from orangebeard.entity.Serializable import Serializable


class Attribute(Serializable):
    def __init__(
            self, key=None, value=None
    ):
        self.key = key
        self.value = value
