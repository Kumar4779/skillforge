from statkit import median


def test_median_of_three():
    assert median([3, 1, 2]) == 2


def test_median_of_five():
    assert median([7, 1, 5, 3, 9]) == 5
