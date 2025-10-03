import os
import json
from typing import List, Optional

from orangebeard.entity.OrangebeardParameters import OrangebeardParameters
from orangebeard.entity.Attribute import Attribute


def get_attributes_from_string(string_attr: str) -> List[Attribute]:
    return [Attribute(*attribute.partition(':')[::2]) for attribute in
            string_attr.split(';')] if string_attr is not None else []


def _create_attribute_objects(attributes_data: Optional[list]) -> List[Attribute]:
    attributes = []
    if attributes_data:
        for item in attributes_data:
            if isinstance(item, dict):  # Handle JSON-style dictionaries
                attributes.append(Attribute(item.get("key"), item.get("value")))
    return attributes


def update_config_parameters_from_env(current_config: OrangebeardParameters) -> OrangebeardParameters:
    current_config.token = os.environ.get('ORANGEBEARD_TOKEN', current_config.token)
    current_config.endpoint = os.environ.get('ORANGEBEARD_ENDPOINT', current_config.endpoint)
    current_config.testset = os.environ.get('ORANGEBEARD_TESTSET', current_config.testset)
    current_config.project = os.environ.get('ORANGEBEARD_PROJECT', current_config.project)
    current_config.description = os.environ.get('ORANGEBEARD_DESCRIPTION', current_config.description)

    current_config.attributes = _create_attribute_objects(current_config.attributes)
    env_attributes = get_attributes_from_string(os.environ.get('ORANGEBEARD_ATTRIBUTES', None))
    if env_attributes:
        current_config.attributes.extend(env_attributes)

    current_config.referenceUrl = os.environ.get('ORANGEBEARD_REFERENCE_URL', current_config.referenceUrl)
    if current_config.referenceUrl is not None:
        current_config.attributes.append(Attribute('reference_url', current_config.referenceUrl))
        current_config.referenceUrl = None #moved to attribute

    current_config.testrun_uuid = os.environ.get('ORANGEBEARD_TESTRUN_UUID', current_config.testrun_uuid)

    return current_config


# noinspection PyBroadException
def get_config(path_to_resolve: str) -> OrangebeardParameters:
    config_from_file = OrangebeardParameters()

    current_path = path_to_resolve
    while True:
        config_file_path = os.path.join(current_path, 'orangebeard.json')
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as file:
                    config_data = json.load(file)
                    if isinstance(config_data, dict):
                        config_from_file.__dict__.update(config_data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not read or parse {config_file_path}. Error: {e}")
            break

        prev_path = current_path
        current_path = os.path.dirname(current_path)

        if current_path == prev_path:
            break

    return update_config_parameters_from_env(config_from_file)


config = get_config(os.getcwd())
