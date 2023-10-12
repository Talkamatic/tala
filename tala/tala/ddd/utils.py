class CacheMethod:
    def __init__(self, instance, method):
        self._method = method
        self._cache = {}

        def cached_method(*args):
            if args in self._cache:
                return self._cache[args]
            else:
                value = self._method.__call__(*args)
                self._cache[args] = value
                return value

        setattr(instance, method.__name__, cached_method)

    def __str__(self):
        return "CacheMethod(%s, _cache=%s)" % (self._method, self._cache)

    def clear(self):
        self._cache = {}
