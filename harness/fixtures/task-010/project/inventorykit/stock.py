"""Stock levels per product."""

STOCK = {
    "widget": 500,
    "sprocket": 300,
    "gadget": 120,
    "gizmo": 800,
    "bolt": 5000,
    "panel": 60,
}


def available(name, qty):
    """Return True if at least `qty` units of `name` are in stock."""
    return STOCK.get(name, 0) >= qty
