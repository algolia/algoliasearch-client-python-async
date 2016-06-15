import asyncio
import unittest
from random import randint

from .helpers import safe_index_name
from .helpers import get_api_client
from .helpers import FakeData
from .helpers import wait_key, wait_missing_key


class KeyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.client = get_api_client()
        cls.index_name = safe_index_name('àlgol?à-python{0}'.format(
                                         randint(1, 1000)))
        cls.index = cls.client.init_index(cls.index_name)
        cls.client.delete_index(cls.index_name)

        cls.factory = FakeData()

    @classmethod
    def tearDownClass(cls):
        cls.loop.run_until_complete(cls.client.close())

    def setUp(self):
        task = self.index.add_objects(self.factory.fake_contact(5))
        self.index.wait_task(task['taskID'])

    def tearDown(self):
        self.client.delete_index(self.index_name)

    def test_list_user_keys(self):
        res = self.client.list_user_keys()
        self.assertIn('keys', res)

    def test_add_user_keys(self):
        keys = []

        res = self.client.add_user_key(['search'])
        self.assertGreater(len(res['key']), 1)
        keys.append(res['key'])

        res = self.client.add_user_key(['search'],
                                       max_queries_per_ip_per_hour=10)
        self.assertGreater(len(res['key']), 1)
        keys.append(res['key'])

        res = self.client.add_user_key(['search'], max_hits_per_query=5)
        self.assertGreater(len(res['key']), 1)
        keys.append(res['key'])

        res = self.client.add_user_key(['search'], validity=30)
        self.assertGreater(len(res['key']), 1)

        for key in keys:
            self.client.delete_user_key(key)

    def test_get_user_key(self):
        res = self.client.add_user_key(['search'])
        key = res['key']
        wait_key(self.client, key)

        res = self.client.get_user_key_acl(key)
        self.assertEqual(res['value'], key)
        self.assertSetEqual(set(res['acl']), set(['search']))

        self.client.delete_user_key(key)

    def test_update_user_keys(self):
        keys = []

        for i in range(3):
            res = self.client.add_user_key(['search'])
            keys.append(res['key'])

        for k in keys:
            wait_key(self.client, k)

        res = self.client.update_user_key(keys[0], ['addObject'],
                                          max_queries_per_ip_per_hour=5)
        self.assertGreater(len(res['key']), 0)
        wait_key(self.client, keys[0], lambda k: k['acl'] == ['addObject'])
        res = self.client.get_user_key_acl(keys[0])
        self.assertSetEqual(set(res['acl']), set(['addObject']))
        self.assertEqual(res['maxQueriesPerIPPerHour'], 5)

        res = self.client.update_user_key(keys[1], ['deleteObject'],
                                          max_hits_per_query=10)
        self.assertGreater(len(res['key']), 0)

        wait_key(self.client, keys[1], lambda k: k['acl'] == ['deleteObject'])
        res = self.client.get_user_key_acl(keys[1])
        self.assertSetEqual(set(res['acl']), set(['deleteObject']))
        self.assertEqual(res['maxHitsPerQuery'], 10)

        res = self.client.update_user_key(keys[2], ['settings', 'search'],
                                          validity=60)
        self.assertGreater(len(res['key']), 0)
        wait_key(self.client, keys[2], lambda k: set(k['acl']) == set(['settings', 'search']))
        res = self.client.get_user_key_acl(keys[2])
        self.assertSetEqual(set(res['acl']), set(['settings', 'search']))
        self.assertIn('validity', res)
        self.assertGreater(res['validity'], 0)

        for key in keys:
            self.client.delete_user_key(key)

    def test_delete_user_keys(self):
        res = self.client.add_user_key(['search'])
        key = res['key']
        wait_key(self.client, res['key'])

        self.client.delete_user_key(key)
        wait_missing_key(self.client, res['key'])

        res = self.client.list_user_keys()
        res_keys = [elt['value'] for elt in res['keys']]
        self.assertNotIn(key, res_keys)

    def test_index_list_user_keys(self):
        res = self.index.list_user_keys()
        self.assertIn('keys', res)

    def test_index_add_user_keys(self):
        keys = []

        res = self.index.add_user_key(['search'])
        self.assertGreater(len(res['key']), 1)
        keys.append(res['key'])

        res = self.index.add_user_key(['search'],
                                      max_queries_per_ip_per_hour=10)
        self.assertGreater(len(res['key']), 1)
        keys.append(res['key'])

        res = self.index.add_user_key(['search'], max_hits_per_query=5)
        self.assertGreater(len(res['key']), 1)
        keys.append(res['key'])

        res = self.index.add_user_key(['search'], validity=30)
        self.assertGreater(len(res['key']), 1)

        for key in keys:
            self.index.delete_user_key(key)

    def test_index_get_user_key(self):
        res = self.index.add_user_key(['search'])
        key = res['key']
        wait_key(self.index, res['key'])

        res = self.index.get_user_key_acl(key)
        self.assertEqual(res['value'], key)
        self.assertSetEqual(set(res['acl']), set(['search']))

        self.index.delete_user_key(key)

    def test_index_update_user_keys(self):
        keys = []

        for i in range(3):
            res = self.index.add_user_key(['search'])
            keys.append(res['key'])

        for k in keys:
            wait_key(self.index, k)

        res = self.index.update_user_key(keys[0], ['addObject'],
                                         max_queries_per_ip_per_hour=5)
        self.assertGreater(len(res['key']), 0)
        wait_key(self.index, keys[0], lambda k: k['acl'] == ['addObject'])
        res = self.index.get_user_key_acl(keys[0])
        self.assertSetEqual(set(res['acl']), set(['addObject']))
        self.assertEqual(res['maxQueriesPerIPPerHour'], 5)

        res = self.index.update_user_key(keys[1], ['deleteObject'],
                                         max_hits_per_query=10)
        self.assertGreater(len(res['key']), 0)
        wait_key(self.index, keys[1], lambda k: k['acl'] == ['deleteObject'])
        res = self.index.get_user_key_acl(keys[1])
        self.assertSetEqual(set(res['acl']), set(['deleteObject']))
        self.assertEqual(res['maxHitsPerQuery'], 10)

        res = self.index.update_user_key(keys[2], ['settings', 'search'],
                                         validity=60)
        self.assertGreater(len(res['key']), 0)
        wait_key(self.index, keys[2], lambda k: set(k['acl']) == set(['search', 'settings']))
        res = self.index.get_user_key_acl(keys[2])
        self.assertSetEqual(set(res['acl']), set(['settings', 'search']))
        self.assertIn('validity', res)
        self.assertGreater(res['validity'], 0)

        for key in keys:
            self.index.delete_user_key(key)

    def test_index_delete_user_keys(self):
        res = self.index.add_user_key(['search'])
        key = res['key']
        wait_key(self.index, res['key'])

        self.index.delete_user_key(key)
        wait_missing_key(self.index, res['key'])

        res = self.index.list_user_keys()
        res_keys = [elt['value'] for elt in res['keys']]
        self.assertNotIn(key, res_keys)
