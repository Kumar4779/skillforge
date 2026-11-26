"""Shipping charges.

Policy (b): shipping is free when the after-discount merchandise subtotal is over $75;
otherwise it is a flat $6.95.
"""

from decimal import Decimal

FREE_SHIPPING_OVER = Decimal("75.00")
FLAT_RATE = Decimal("6.95")


def shipping_cost(lines):
    """Return the shipping charge for an order. `lines` holds (name, unit_price, qty)."""
    subtotal = sum((unit_price * qty for _name, unit_price, qty in lines), Decimal("0"))
    return Decimal("0.00") if subtotal > FREE_SHIPPING_OVER else FLAT_RATE
