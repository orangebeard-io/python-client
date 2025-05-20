import os
import json
import unittest
import tempfile
from orangebeard.config import AutoConfig
from orangebeard.entity.OrangebeardParameters import OrangebeardParameters

class TestAutoConfig(unittest.TestCase):
    def test_get_attributes_from_string(self):
        attrs = AutoConfig.get_attributes_from_string('a:1;b')
        self.assertEqual(len(attrs), 2)
        self.assertEqual(attrs[0].key, 'a')
        self.assertEqual(attrs[0].value, '1')
        self.assertIsNone(attrs[1].key)
        self.assertEqual(attrs[1].value, 'b')

    def test_get_config_reads_file_and_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                'token': 'filetoken',
                'endpoint': 'fileend',
                'testset': 'fileset',
                'project': 'fileproj',
                'description': 'desc'
            }
            with open(os.path.join(tmp, 'orangebeard.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f)
            os.environ['ORANGEBEARD_TOKEN'] = 'envtoken'
            cfg = AutoConfig.get_config(tmp)
            self.assertEqual(cfg.token, 'envtoken')
            self.assertEqual(cfg.endpoint, 'fileend')
            self.assertEqual(cfg.project, 'fileproj')
            del os.environ['ORANGEBEARD_TOKEN']

# end test
