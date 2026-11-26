from decimal import Decimal

from inventorykit import create_order, daily_summary, order_total


def test_small_order_pays_shipping_and_tax():
    # 2 x 7.80 = 15.60; shipping 6.95; tax 1.248 -> 23.798 -> 23.80
    assert order_total(create_order([("widget", 2)])) == Decimal("23.80")


def test_large_order_without_bulk_lines_ships_free():
    # 2 x 45.00 = 90.00; free shipping; tax 7.20 -> 97.20
    assert order_total(create_order([("panel", 2)])) == Decimal("97.20")


def test_daily_summary_counts_orders_units_and_revenue():
    orders = [create_order([("widget", 2)]), create_order([("panel", 2), ("gizmo", 1)])]
    summary = daily_summary(orders)
    assert summary["orders"] == 2
    assert summary["units"] == 5
    assert summary["revenue"] == order_total(orders[0]) + order_total(orders[1])
