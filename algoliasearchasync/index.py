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
    'browse_from',
]

class AsyncIndexIterator:
    def __init__(self, index, params=None):
        if params is None:
            params = {}

        self.index = index
        self.params = params
        self.cursor = None

    @asyncio.coroutine
    def __aiter__(self):
        yield from self._load_next_page()
        return self

    @asyncio.coroutine
    def __anext__(self):
        return self._next()

    @asyncio.coroutine
    def _next(self):
        while True:
            if self.pos < len(self.answer['hits']):
                self.pos += 1
                return self.answer['hits'][self.pos - 1]
            elif self.cursor:
                yield from self._load_next_page()
                continue
            else:
                raise StopAsyncIteration

    @asyncio.coroutine
    def _load_next_page(self):
        self.answer = yield from self.index.browse_from_async(self.params, self.cursor)
        self.pos = 0
        self.cursor = self.answer.get('cursor', None)


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

    @asyncio.coroutine
    def delete_by_query_async(self, query, params=None):
        if params is None:
            params = {}

        params['query'] = query
        params['hitsPerPage'] = 1000
        params['attributesToRetrieve'] = ['objectID']
        params['attributesToSnippet'] = []
        params['attributesToHighlight'] = []
        params['distinct'] = []

        ids = []
        iterator = yield from AsyncIndexIterator(self, params).__aiter__()

        try:
            while True:
                next = yield from iterator.__anext__()
                ids.append(next['objectID'])
        except StopAsyncIteration:
            pass

        return (yield from self.delete_objects_async(ids))

    def browse_all_async(self, params=None):
        return AsyncIndexIterator(self, params=params)
