from algoliasearch.client import Client

import asyncio

from .helpers import gen_async, gen_forward, gen_sync
from .index import IndexAsync
from .transport import Transport
from .version import __version__

USER_AGENT = "; async ({})".format(__version__)

CLIENT_ASYNC_METHODS = [
    'add_user_key',
    'batch',
    'copy_index',
    'delete_index',
    'delete_user_key',
    'get_logs',
    'get_user_key_acl',
    'list_indexes',
    'list_user_keys',
    'move_index',
    'multiple_queries',
    'update_user_key',
]

CLIENT_FORWARD_METHODS = [
    'enable_rate_limit_forward',
    'disable_rate_limit_forward',
    'set_end_user_ip',
    'generate_secured_api_key',
]


class ClientAsync(object):
    def __init__(self, app_id, api_key, hosts_array=None):
        t = Transport()
        self._base = Client(app_id, api_key, hosts_array, t)
        t.headers['User-Agent'] += USER_AGENT

        for method in CLIENT_ASYNC_METHODS:
            setattr(self, method + '_async', gen_async(self, method))
            setattr(self, method, gen_sync(self, method))

        for method in CLIENT_FORWARD_METHODS:
            setattr(self, method, gen_forward(self, method))

    def init_index(self, name):
        return IndexAsync(self._base, name)

    def set_extra_headers(self, **kwargs):
        hstr = {k: str(v) for k, v in kwargs.items()}
        self._base._transport.headers.update(hstr)

    @asyncio.coroutine
    def set_conn_timeout(self, t):
        yield from self._base._transport.set_conn_timeout(t)

    @asyncio.coroutine
    def close(self):
        yield from self._base._transport.close()

    @asyncio.coroutine
    def __aenter__(self):
        return self

    @asyncio.coroutine
    def __aexit__(self, exc_type, exc, tb):
        yield from self.close()

    # Client properties.
    @property
    def app_id(self):
        return self._base.app_id

    @property
    def api_key(self):
        return self._base.api_key

    @api_key.setter
    def api_key(self, k):
        self._base.api_key = k

    @property
    def headers(self):
        return self._base.headers
