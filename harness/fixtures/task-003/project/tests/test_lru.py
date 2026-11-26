from cachekit import LRUCache


def test_put_then_get():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_holds_up_to_capacity():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
