from statkit import median


def test_even_length_ints_average_the_two_middles():
    assert median([4, 1, 3, 2]) == 2.5


def test_even_length_floats():
    assert median([3.5, 0.5, 2.5, 1.5]) == 2.0


def test_odd_length():
    assert median([9, 3, 7]) == 7


def test_single_element():
    assert median([42]) == 42


def test_input_list_is_not_mutated():
    data = [3, 1, 4, 2]
    median(data)
    assert data == [3, 1, 4, 2]
