import asyncio

from .helpers import gen_async, gen_sync

INDEX_ASYNC_METHODS = [
    'add_object',
    'add_objects',
    'add_user_key',
    'batch',
    'batch_synonyms',
    'clear_index',
    'clear_synonyms',
    'delete_object',
    'delete_objects',
    'delete_synonym',
    'delete_user_key',
    'get_object',
    'get_objects',
    'get_settings',
    'get_synonym',
    'get_user_key_acl',
    'list_user_keys',
    'partial_update_object',
    'partial_update_objects',
    'save_object',
    'save_objects',
    'save_synonym',
    'search',
    'search_for_facet_values',
    'search_synonyms',
    'set_settings',
    'update_user_key',
]


class IndexAsync:
    def __init__(self, client, name):
        self._base = client.init_index(name)

        for method in INDEX_ASYNC_METHODS:
            setattr(self, method + '_async', gen_async(self, method))
            setattr(self, method, gen_sync(self, method))

        setattr(self, 'wait_task', gen_sync(self, 'wait_task'))

    @asyncio.coroutine
    def wait_task_async(self, task_id, time_before_retry=100):
        path = '/task/%d' % task_id
        while True:
            res = yield from self._base._req(True, path, 'GET')
            if res['status'] == 'published':
                return res
            yield from asyncio.sleep(time_before_retry / 1000)
