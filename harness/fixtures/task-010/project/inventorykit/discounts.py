"""Bulk discounts.

Policy (a): 5% off any line with quantity >= 10.
"""

from decimal import Decimal

BULK_QUANTITY = 10
BULK_RATE = Decimal("0.05")


def line_total(unit_price, qty):
    """Return the price of one order line after any bulk discount."""
    total = unit_price * qty
    if qty > BULK_QUANTITY:
        total -= total * BULK_RATE
    return total


def discounted_subtotal(lines):
    """Return the after-discount merchandise subtotal. `lines` holds (name, unit_price, qty)."""
    return sum((line_total(unit_price, qty) for _name, unit_price, qty in lines), Decimal("0"))
