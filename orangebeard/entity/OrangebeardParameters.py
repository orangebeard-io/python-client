from orangebeard.entity.Serializable import Serializable


class OrangebeardParameters(Serializable):
    def __init__(self,
                 token=None,
                 endpoint=None,
                 testset=None,
                 project=None,
                 description=None,
                 attributes=None,
                 ref_url=None
                 ):
        self.token = token
        self.endpoint = endpoint
        self.testset = testset
        self.project = project
        self.description = description
        self.attributes = attributes
        self.ref_url = ref_url
