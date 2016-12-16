import json
import time

import aiohttp
import asyncio
from algoliasearch.helpers import AlgoliaException, CustomJSONEncoder, urlify, rotate


DNS_TIMER_DELAY = 5 * 60  # 5 minutes


class Transport:
    def __init__(self):
        self.headers = {}
        self.read_hosts = []
        self.write_hosts = []

        self._dns_timer = 0
        self._conn_timeout = 2
        self.timeout = 30
        self.search_timeout = 5

        self._init_session()

    def _init_session(self):
        connector = aiohttp.TCPConnector(conn_timeout=self.conn_timeout, use_dns_cache=False)
        self.session = aiohttp.ClientSession(connector=connector)

    @property
    def read_hosts(self):
        return self._read_hosts

    @read_hosts.setter
    def read_hosts(self, value):
        self._read_hosts = value
        self._original_read_hosts = value

    @property
    def write_hosts(self):
        return self._write_hosts

    @write_hosts.setter
    def write_hosts(self, value):
        self._write_hosts = value
        self._original_write_hosts = value

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

        hosts = self._get_hosts(is_search)
        timeout = self.search_timeout if is_search else self.timeout

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
                self._rotate_hosts(is_search)
                self._dns_timer = time.time()
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

    def _get_hosts(self, is_search):
        secs_since_rotate = time.time() - self._dns_timer
        if is_search:
            if secs_since_rotate < DNS_TIMER_DELAY:
                return self.read_hosts
            else:
                return self._original_read_hosts
        else:
            if secs_since_rotate < DNS_TIMER_DELAY:
                return self.write_hosts
            else:
                return self._original_write_hosts

    def _rotate_hosts(self, is_search):
        if is_search:
            self._read_hosts = rotate(self.read_hosts)
        else:
            self._write_hosts = rotate(self.write_hosts)
