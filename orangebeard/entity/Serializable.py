import json


class Serializable:
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
