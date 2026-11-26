"""Pricing rules for the cart.

Policy, applied in this order:

1. Promo: buy 2, get 1 free. For each item, every third unit of that item is free.
2. Coupon: a $5 coupon applies only if the after-promo subtotal is strictly over $40.
"""

COUPON_AMOUNT = 5
COUPON_THRESHOLD = 40


def apply_promo(lines):
    """Return the subtotal after the promo. `lines` is an iterable of (name, price, qty)."""
    return sum(price * (qty - qty // 3) for _name, price, qty in lines)


def apply_coupon(subtotal):
    """Return the coupon discount earned by `subtotal`: COUPON_AMOUNT if over the threshold, else 0."""
    return COUPON_AMOUNT if subtotal > COUPON_THRESHOLD else 0
