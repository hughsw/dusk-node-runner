import asyncio
import functools
import time

import requests

printio = functools.partial(asyncio.to_thread, print)
getio = functools.partial(asyncio.to_thread, requests.get)
postio = functools.partial(asyncio.to_thread, requests.post)

class attrdict(dict):
    # Access dict fields with dot notation.
    # Good enough for JSON work, but doesn't play well with introspective tools, e.g. pydantic.
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value): self[key] = value
    def __delattr__(self, key): del self[key]

    @staticmethod
    def deep(obj):
        def obj_recurse(obj):
            if isinstance(obj, tuple): return tuple(obj_recurse(item) for item in obj)
            if isinstance(obj, list): return list(obj_recurse(item) for item in obj)
            if isinstance(obj, dict): return attrdict((key, obj_recurse(value)) for key, value in obj.items())
            return obj
        return obj_recurse(obj)

# decorator for caching for a timeout
def caching(timeout_sec, *, monotonic = time.monotonic):
    assert timeout_sec >= 0, str((timeout_sec, func))

    def wrap(func):
        cache = attrdict(
            valid_until = monotonic() - 1,
            value = None,
            )
        async def wrapping(*args, **kwargs):
            if monotonic() > cache.valid_until:
                cache.value = await func(*args, **kwargs)
                cache.valid_until = monotonic() + timeout_sec
            return cache.value
        return wrapping

    return wrap

# decorator to asyncify a funtion
def asyncify(func):
    funcio = functools.partial(asyncio.to_thread, func)
    async def wrapping(*args, **kwargs):
        result = await funcio(*args, **kwargs)

        return result

    return wrapping
