"""A small order system: catalog, stock, orders, and pricing.

Pricing policy (see discounts.py, shipping.py, tax.py, and orders.py):

(a) Bulk discount: 5% off any line with quantity >= 10.
(b) Shipping: free when the after-discount merchandise subtotal is over $75; otherwise $6.95.
(c) Tax: 8% on the after-discount merchandise subtotal only, not on shipping.
order_total rounds half-up to cents at the end.
"""

from inventorykit.orders import create_order, order_total
from inventorykit.reports import daily_summary

__all__ = ["create_order", "daily_summary", "order_total"]
