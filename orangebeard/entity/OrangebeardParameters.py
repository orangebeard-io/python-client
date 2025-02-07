from orangebeard.entity.Serializable import Serializable


class OrangebeardParameters(Serializable):
    def __init__(self,
                 token=None,
                 endpoint=None,
                 testset=None,
                 project=None,
                 description=None,
                 attributes=None,
                 reference_url=None,
                 testrun_uuid=None
                 ):
        self.token = token
        self.endpoint = endpoint
        self.testset = testset
        self.project = project
        self.description = description
        self.attributes = attributes or []
        self.referenceUrl = reference_url
        self.testrun_uuid = testrun_uuid
