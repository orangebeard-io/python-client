import json


class Serializable:

    def __remove_none_values(self):
        return {key: value for key, value in self.__dict__.items() if value is not None}

    def to_json(self):
        return json.dumps(self.__remove_none_values(), default=lambda o: o.__dict__)
