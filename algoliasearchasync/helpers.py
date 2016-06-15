import asyncio


def gen_async(s, method):
    m = getattr(s._base, method)

    def async_(*args, **kwargs):
        return m(*args, **kwargs)

    return asyncio.coroutine(async_)


def gen_sync(s, method):
    m = getattr(s, method + '_async')

    def sync(*args, **kwargs):
        l = kwargs.get('event_loop', asyncio.get_event_loop())
        if 'event_loop' in kwargs:
            kwargs = kwargs.copy()
            del kwargs['event_loop']
        return l.run_until_complete(m(*args, **kwargs))

    return sync


def gen_forward(s, method):
    m = getattr(s._base, method)

    def forward(*args, **kwargs):
        return m(*args, **kwargs)

    return forward
