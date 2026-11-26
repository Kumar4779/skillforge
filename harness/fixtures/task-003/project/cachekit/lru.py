"""A fixed-capacity least-recently-used cache."""

from collections import OrderedDict


class LRUCache:
    """Holds up to `capacity` items, evicting the least recently used one when full."""

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._items = OrderedDict()

    def get(self, key):
        """Return the value for `key`, or None if it is not cached."""
        return self._items.get(key)

    def put(self, key, value):
        """Store `value` under `key`, evicting the least recently used item if full."""
        if key in self._items:
            self._items.move_to_end(key)
        self._items[key] = value
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def __len__(self):
        return len(self._items)
