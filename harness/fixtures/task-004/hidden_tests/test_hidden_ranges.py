from rangekit import overlaps


def test_touching_at_the_end():
    assert overlaps(1, 3, 3, 5) is True


def test_touching_at_the_start():
    assert overlaps(3, 5, 1, 3) is True


def test_one_range_inside_another():
    assert overlaps(1, 10, 4, 6) is True
    assert overlaps(4, 6, 1, 10) is True


def test_identical_ranges():
    assert overlaps(2, 6, 2, 6) is True


def test_single_point_range_inside_a_range_containing_it():
    assert overlaps(1, 1, 1, 9) is True
    assert overlaps(9, 9, 1, 9) is True
    assert overlaps(5, 5, 1, 9) is True


def test_disjoint_ranges_still_do_not_overlap():
    assert overlaps(1, 3, 4, 5) is False
    assert overlaps(4, 5, 1, 3) is False
    assert overlaps(1, 2, 6, 9) is False
