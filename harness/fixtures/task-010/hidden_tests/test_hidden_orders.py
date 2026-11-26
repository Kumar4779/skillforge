from decimal import Decimal

from inventorykit import create_order, order_total


def total(*lines):
    return order_total(create_order(list(lines)))


def test_reported_combined_case():
    # 78.00 -> 5% off -> 74.10 (not over 75: shipping 6.95); tax 5.928 -> 86.978 -> 86.98
    assert total(("widget", 10)) == Decimal("86.98")


def test_discount_boundary_only_far_from_shipping_threshold():
    # 10 x 0.40 = 4.00 -> 3.80; shipping 6.95; tax 0.304 -> 11.054 -> 11.05
    assert total(("bolt", 10)) == Decimal("11.05")
    # 10 x 45.00 = 450.00 -> 427.50; free shipping; tax 34.20 -> 461.70
    assert total(("panel", 10)) == Decimal("461.70")


def test_shipping_threshold_only_with_quantity_12():
    # 12 x 6.50 = 78.00 -> 74.10 after discount, not over 75: shipping 6.95; tax 5.928 -> 86.98
    assert total(("sprocket", 12)) == Decimal("86.98")


def test_clearly_free_shipping():
    # 20 x 7.80 = 156.00 -> 148.20; free shipping; tax 11.856 -> 160.056 -> 160.06
    assert total(("widget", 20)) == Decimal("160.06")


def test_no_discount_with_shipping_charged():
    # 3 x 3.25 = 9.75; shipping 6.95; tax 0.78 -> 17.48
    assert total(("gizmo", 3)) == Decimal("17.48")
