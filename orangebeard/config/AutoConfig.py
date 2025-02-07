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

    current_config.referenceUrl = os.environ.get('ORANGEBEARD_REF_URL', current_config.referenceUrl)
    if current_config.referenceUrl is not None:
        current_config.attributes.append(Attribute('reference_url', current_config.referenceUrl))

    current_config.testrun_uuid = os.environ.get('ORANGEBEARD_TESTRUN_UUID', current_config.testrun_uuid)

    return current_config


# noinspection PyBroadException
def get_config(path_to_resolve: str) -> Optional[OrangebeardParameters]:
    traversing = True
    configuration = OrangebeardParameters()
    while traversing:
        config_file_path = os.path.join(path_to_resolve, 'orangebeard.json')
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as file:
                    config_data = json.load(file)
                    if not isinstance(config_data, dict):
                        config_data = None
                    configuration.__dict__.update(config_data)
                    break
            except Exception:
                pass

        prev_path = path_to_resolve
        path_to_resolve = os.path.dirname(path_to_resolve)

        traversing = path_to_resolve != prev_path

    return update_config_parameters_from_env(configuration)


config = get_config(os.getcwd())
