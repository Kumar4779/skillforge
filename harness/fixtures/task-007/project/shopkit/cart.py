"""A shopping cart that prices its contents with shopkit.pricing."""

from shopkit.pricing import apply_coupon, apply_promo


class Cart:
    def __init__(self, coupon=False):
        self.coupon = coupon
        self._lines = {}  # name -> [unit price, quantity]

    def add(self, name, price, qty=1):
        if name in self._lines:
            self._lines[name][1] += qty
        else:
            self._lines[name] = [price, qty]

    def subtotal(self):
        """Price of everything in the cart before any promo or coupon."""
        return sum(price * qty for price, qty in self._lines.values())

    def total(self):
        lines = [(name, price, qty) for name, (price, qty) in self._lines.items()]
        after_promo = apply_promo(lines)
        discount = apply_coupon(self.subtotal()) if self.coupon else 0
        return after_promo - discount
