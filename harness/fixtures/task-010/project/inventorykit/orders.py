"""Orders and order totals.

order_total = after-discount merchandise + shipping + tax, rounded half-up to cents at the end.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from inventorykit.discounts import discounted_subtotal
from inventorykit.products import price_of
from inventorykit.shipping import shipping_cost
from inventorykit.stock import available
from inventorykit.tax import tax_on

CENT = Decimal("0.01")


@dataclass
class Order:
    lines: list = field(default_factory=list)  # (name, unit_price, qty)


def create_order(lines):
    """Build an Order from (name, qty) pairs. Raises ValueError if a product is out of stock."""
    order = Order()
    for name, qty in lines:
        if qty < 1:
            raise ValueError(f"quantity must be at least 1: {name}")
        if not available(name, qty):
            raise ValueError(f"not enough stock: {name}")
        order.lines.append((name, price_of(name), qty))
    return order


def order_total(order):
    """Return the amount charged for `order`, in dollars, rounded half-up to cents."""
    merchandise = discounted_subtotal(order.lines)
    total = merchandise + shipping_cost(order.lines) + tax_on(merchandise)
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
