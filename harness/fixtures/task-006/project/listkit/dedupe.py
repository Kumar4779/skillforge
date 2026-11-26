"""List helpers."""


def dedupe_sorted(values):
    """Return a new list of the unique items in `values`, sorted."""
    values.sort()
    unique = []
    for item in values:
        if not unique or unique[-1] != item:
            unique.append(item)
    values[:] = unique
    return values
