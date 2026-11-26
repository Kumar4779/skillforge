"""Daily reporting."""

from decimal import Decimal

from inventorykit.orders import order_total


def daily_summary(orders):
    """Return {"orders": count, "units": total units, "revenue": sum of order totals}."""
    return {
        "orders": len(orders),
        "units": sum(qty for order in orders for _name, _price, qty in order.lines),
        "revenue": sum((order_total(order) for order in orders), Decimal("0.00")),
    }
