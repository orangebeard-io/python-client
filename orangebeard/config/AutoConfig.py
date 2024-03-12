import os
import json
from typing import List, Optional

from orangebeard.entity.OrangebeardParameters import OrangebeardParameters
from orangebeard.entity.Attribute import Attribute


def get_attributes_from_string(string_attr: str) -> List[Attribute]:
    return [Attribute(*attribute.split(':')) if ':' in attribute else Attribute(None, attribute) for attribute in
            string_attr.split(';')]


def update_config_parameters_from_env(current_config: OrangebeardParameters) -> OrangebeardParameters:
    current_config.token = os.environ.get('ORANGEBEARD_TOKEN', current_config.token)
    current_config.endpoint = os.environ.get('ORANGEBEARD_ENDPOINT', current_config.endpoint)
    current_config.testset = os.environ.get('ORANGEBEARD_TESTSET', current_config.testset)
    current_config.project = os.environ.get('ORANGEBEARD_PROJECT', current_config.project)
    current_config.description = os.environ.get('ORANGEBEARD_DESCRIPTION', current_config.description)
    current_config.attributes = get_attributes_from_string(
        os.environ.get('ORANGEBEARD_ATTRIBUTES', '')) if os.environ.get(
        'ORANGEBEARD_ATTRIBUTES') else current_config.attributes
    current_config.ref_url = os.environ.get('ORANGEBEARD_REF_URL', current_config.ref_url)

    return current_config


# noinspection PyBroadException
def get_config(path_to_resolve: str) -> Optional[OrangebeardParameters]:
    traversing = True
    while traversing:
        config_file_path = os.path.join(path_to_resolve, 'orangebeard.json')
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as file:
                    config_data = json.load(file)
                    if not isinstance(config_data, dict):
                        config_data = None
                    config_from_file = OrangebeardParameters()
                    config_from_file.__dict__.update(config_data)
                    return update_config_parameters_from_env(config_from_file)
            except Exception:
                return update_config_parameters_from_env(OrangebeardParameters())

        prev_path = path_to_resolve
        path_to_resolve = os.path.dirname(path_to_resolve)

        traversing = path_to_resolve != prev_path

    return update_config_parameters_from_env(OrangebeardParameters())


config = get_config(os.getcwd())
