import os
import time
from random import randint

from faker import Factory

from algoliasearchasync.client import ClientAsync


class FakeData(object):
    def __init__(self):
        self._fake = Factory.create('zh_CN')
        self._fake.seed(4242)
        self._generated_id = []

    def fake_contact(self, n=1):
        data = []
        for i in range(n):
            data.append({
                'name': self._fake.name(),
                'email': self._fake.email(),
                'phone': self._fake.phone_number(),
                'city': self._fake.city(),
                'country': self._fake.country()
            })

        return data[0] if n == 1 else data

    def generate_id(self):
        while True:
            new_id = randint(0, 100000)
            if new_id not in self._generated_id:
                self._generated_id.append(new_id)
                return str(new_id)


def get_api_client():
    return ClientAsync(
        os.environ['ALGOLIA_APPLICATION_ID'],
        os.environ['ALGOLIA_API_KEY'],
    )


def safe_index_name(name):
    if 'TRAVIS' not in os.environ:
        return name
    job = os.environ['TRAVIS_JOB_NUMBER']
    return '{0}_travis-{1}'.format(name, job)


def wait_key(index, key, block=None):
    for i in range(60):
        try:
            k = index.get_user_key_acl(key)
            if block is None or block(k):
                return
        except:
            pass
        # Not found.
        time.sleep(1)


def wait_missing_key(index, key):
    for i in range(60):
        try:
            index.get_user_key_acl(key)
            time.sleep(1)
        except:
            # Not found.
            return
