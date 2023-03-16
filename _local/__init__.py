from threading import local

__INSTANCES = local()


def currentClient():
    if hasattr(__INSTANCES, 'current'):
        return __INSTANCES.currentClient


def set_currentClient(orangbeardClient):
    __INSTANCES.currentClient = orangbeardClient
