import json

import aiohttp
import asyncio
from algoliasearch.helpers import AlgoliaException, CustomJSONEncoder, urlify


class Transport:
    def __init__(self):
        self.headers = {}
        self.read_hosts = []
        self.write_hosts = []

        self._conn_timeout = 2
        self.timeout = 30
        self.search_timeout = 5

        self._init_session()

    def _init_session(self):
        connector = aiohttp.TCPConnector(conn_timeout=self.conn_timeout)
        self.session = aiohttp.ClientSession(connector=connector)

    @property
    def conn_timeout(self):
        return self._conn_timeout

    @asyncio.coroutine
    def set_conn_timeout(self, t):
        if not self.session.closed:
            yield from self.session.close()
        self._conn_timeout = t
        self._init_session()

    @asyncio.coroutine
    def close(self):
        if not self.session.closed:
            yield from self.session.close()

    @asyncio.coroutine
    def req(self, is_search, path, meth, params=None, data=None):
        """Perform an HTTPS request with retry logic."""
        if params is not None:
            params = urlify(params)

        if data is not None:
            data = json.dumps(data, cls=CustomJSONEncoder)

        if is_search:
            timeout = self.search_timeout
            hosts = self.read_hosts
        else:
            timeout = self.timeout
            hosts = self.write_hosts

        exceptions = {}
        for i, host in enumerate(hosts):
            old_timeout = None
            if i > 1:
                timeout += 10
                old_timeout = self.conn_timeout
                yield from self.set_conn_timeout(self.conn_timeout + 2)

            try:
                coro = self._req(host, path, meth, timeout, params, data)
                return (yield from coro)
            except AlgoliaException as e:
                raise e
            # TODO: Handle task canceling.
            except Exception as e:
                exceptions[host] = '%s: %s' % (e.__class__.__name__, str(e))
            finally:
                if old_timeout is not None:
                    yield from self.set_conn_timeout(old_timeout)

        raise AlgoliaException('Unreachable hosts: %s', exceptions)

    @asyncio.coroutine
    def _req(self, host, path, meth, timeout, params, data):
        """Perform an HTTPS request with aiohttp's ClientSession."""
        url = 'https://%s%s' % (host, path)
        req = self.session.request(meth, url, params=params, data=data,
                                   headers=self.headers)
        res = yield from req
        with aiohttp.Timeout(timeout):
            if res.status // 100 == 2:
                return (yield from res.json())
            elif res.status // 100 == 4:
                message = 'HTTP Code: %d' % res.status
                try:
                    message = (yield from res.json())['message']
                finally:
                    raise AlgoliaException(message)
        # TODO: Check this for replacement.
        res.raise_for_status()
