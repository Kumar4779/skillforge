from shopkit import Cart


def test_reported_boundary_case_no_coupon_at_exactly_40():
    cart = Cart(coupon=True)
    cart.add("mug", 10, 3)
    cart.add("mug", 10, 2)
    assert cart.total() == 40


def test_coupon_applies_when_clearly_over_threshold_after_promo():
    cart = Cart(coupon=True)
    cart.add("lamp", 25, 3)
    assert cart.total() == 45


def test_coupon_does_not_apply_when_promo_drops_subtotal_below_threshold():
    cart = Cart(coupon=True)
    cart.add("plate", 14, 3)
    assert cart.total() == 28


def test_promo_without_coupon():
    cart = Cart()
    cart.add("pen", 2, 6)
    assert cart.total() == 8


def test_coupon_without_promo():
    over = Cart(coupon=True)
    over.add("book", 45, 1)
    assert over.total() == 40
    under = Cart(coupon=True)
    under.add("book", 30, 1)
    assert under.total() == 30


def test_quantities_that_do_and_do_not_complete_a_group_of_three():
    for qty, expected in [(1, 10), (2, 20), (3, 20), (4, 30), (5, 40), (6, 40)]:
        cart = Cart()
        cart.add("cup", 10, qty)
        assert cart.total() == expected, qty
