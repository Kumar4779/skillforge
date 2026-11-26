from shopkit import Cart


def test_single_item_total():
    cart = Cart()
    cart.add("pen", 2, 2)
    assert cart.total() == 4


def test_promo_makes_third_unit_free():
    cart = Cart()
    cart.add("mug", 10, 3)
    assert cart.total() == 20
