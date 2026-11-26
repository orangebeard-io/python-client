import json

import pytest

from orangebeard.config.AutoConfig import get_attributes_from_string, get_config


def pairs(attributes):
    return [(attribute.key, attribute.value) for attribute in attributes]


@pytest.mark.parametrize('text, expected', [
    ('smoke', [(None, 'smoke')]),
    ('env:acceptance', [('env', 'acceptance')]),
    ('smoke;env:acceptance', [(None, 'smoke'), ('env', 'acceptance')]),
    ('url:https://ci.example/1', [('url', 'https://ci.example/1')]),
    ('smoke;', [(None, 'smoke')]),
    ('smoke; ;fast', [(None, 'smoke'), (None, 'fast')]),
    (';;', []),
    ('', []),
    (None, []),
])
def test_attributes_from_string(text, expected):
    assert pairs(get_attributes_from_string(text)) == expected


def test_a_tag_is_sent_without_a_key():
    assert json.loads(get_attributes_from_string('smoke')[0].to_json()) == {'value': 'smoke'}


def test_tags_from_the_environment_are_added_to_those_from_the_file(tmp_path, monkeypatch):
    monkeypatch.delenv('ORANGEBEARD_REFERENCE_URL', raising=False)
    monkeypatch.setenv('ORANGEBEARD_ATTRIBUTES', 'smoke;')
    (tmp_path / 'orangebeard.json').write_text('{"attributes": [{"key": "team", "value": "web"}]}')
    assert pairs(get_config(str(tmp_path)).attributes) == [('team', 'web'), (None, 'smoke')]
