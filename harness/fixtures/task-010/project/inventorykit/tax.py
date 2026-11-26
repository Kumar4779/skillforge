"""Sales tax.

Policy (c): 8% on the after-discount merchandise subtotal only. Shipping is not taxed.
"""

from decimal import Decimal

TAX_RATE = Decimal("0.08")


def tax_on(merchandise_subtotal):
    """Return the (unrounded) tax due on an after-discount merchandise subtotal."""
    return merchandise_subtotal * TAX_RATE
