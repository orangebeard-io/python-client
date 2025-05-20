import unittest
from orangebeard.entity.Serializable import Serializable

class Dummy(Serializable):
    def __init__(self, a, b):
        self.a = a
        self.b = b

class TestSerializable(unittest.TestCase):
    def test_getitem_and_to_json(self):
        d = Dummy(1, 'two')
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 'two')
        with self.assertRaises(KeyError):
            _ = d['missing']
        json_str = d.to_json()
        self.assertIn('"a": 1', json_str)
        self.assertIn('"b": "two"', json_str)

if __name__ == '__main__':
    unittest.main()
