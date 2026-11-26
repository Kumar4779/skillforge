from sessionkit import create_session, is_valid

START = 1_000_000


def test_valid_at_30_minutes():
    assert is_valid(create_session("u1", START), START + 30 * 60) is True


def test_valid_at_59_minutes():
    assert is_valid(create_session("u1", START), START + 59 * 60) is True


def test_invalid_at_61_minutes():
    assert is_valid(create_session("u1", START), START + 61 * 60) is False


def test_custom_ttl_minutes():
    session = create_session("u1", START, ttl_minutes=2)
    assert is_valid(session, START + 100) is True
    assert is_valid(session, START + 130) is False
