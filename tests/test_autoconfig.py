import os
from orangebeard.entity.Attribute import Attribute
from orangebeard.entity.OrangebeardParameters import OrangebeardParameters
from orangebeard.config.AutoConfig import get_attributes_from_string, update_config_parameters_from_env

def test_get_attributes_from_string():
    attrs = get_attributes_from_string("key1:val1;tag2")
    assert len(attrs) == 2
    assert isinstance(attrs[0], Attribute)
    assert attrs[0].key == "key1"
    assert attrs[0].value == "val1"
    assert attrs[1].key is None
    assert attrs[1].value == "tag2"


def test_update_config_parameters_from_env_reads_attributes(monkeypatch):
    monkeypatch.setenv("ORANGEBEARD_ATTRIBUTES", "key1:val1;tag2")
    params = OrangebeardParameters(attributes=None)
    updated = update_config_parameters_from_env(params)
    assert updated.attributes is not None
    assert len(updated.attributes) == 2
    assert updated.attributes[0].key == "key1"
    assert updated.attributes[0].value == "val1"
    assert updated.attributes[1].key is None
    assert updated.attributes[1].value == "tag2"
