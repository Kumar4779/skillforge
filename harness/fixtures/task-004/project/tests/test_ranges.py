from rangekit import overlaps


def test_clearly_overlapping_ranges():
    assert overlaps(1, 5, 3, 8) is True


def test_clearly_disjoint_ranges():
    assert overlaps(1, 2, 6, 9) is False
