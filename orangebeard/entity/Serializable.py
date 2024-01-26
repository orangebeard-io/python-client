import json
from uuid import UUID


class Serializable:

    def __make_serializable(self):
        serializable_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, UUID):
                serializable_dict[key] = str(value)
            else:
                if value is not None:
                    serializable_dict[key] = value
        return serializable_dict

    def to_json(self):
        return json.dumps(self.__make_serializable(), default=lambda o: o.__dict__)
