from listkit import dedupe_sorted


def test_removes_duplicates_and_sorts():
    assert dedupe_sorted([2, 1, 2]) == [1, 2]


def test_single_item():
    assert dedupe_sorted([5]) == [5]
