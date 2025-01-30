from orangebeard.entity.Serializable import Serializable


class Attribute(Serializable):
    def __init__(self, key=None, value=None):
        if value is None:  # If only one argument is passed, treat it as a value
            self.key = None
            self.value = key
        else:
            self.key = key
            self.value = value
