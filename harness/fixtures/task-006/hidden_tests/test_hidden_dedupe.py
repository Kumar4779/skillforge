from listkit import dedupe_sorted


def test_return_value_with_duplicates():
    assert dedupe_sorted([3, 1, 3, 2, 1]) == [1, 2, 3]


def test_input_list_unchanged_after_call():
    data = [3, 1, 3, 2]
    result = dedupe_sorted(data)
    assert data == [3, 1, 3, 2]
    assert result is not data


def test_empty_list():
    assert dedupe_sorted([]) == []


def test_already_sorted_input_unchanged():
    data = [1, 2, 2, 3]
    assert dedupe_sorted(data) == [1, 2, 3]
    assert data == [1, 2, 2, 3]
