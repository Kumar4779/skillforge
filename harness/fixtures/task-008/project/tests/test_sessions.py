from sessionkit import create_session, is_valid

START = 1_000_000


def test_fresh_session_is_valid():
    session = create_session("u1", START)
    assert is_valid(session, START) is True


def test_session_is_invalid_two_hours_later():
    session = create_session("u1", START)
    assert is_valid(session, START + 2 * 3600) is False
