"""Product catalog: name -> unit price in dollars."""

from decimal import Decimal

CATALOG = {
    "widget": Decimal("7.80"),
    "sprocket": Decimal("6.50"),
    "gadget": Decimal("12.50"),
    "gizmo": Decimal("3.25"),
    "bolt": Decimal("0.40"),
    "panel": Decimal("45.00"),
}


def price_of(name):
    """Return the unit price of `name`. Raises KeyError for unknown products."""
    try:
        return CATALOG[name]
    except KeyError:
        raise KeyError(f"unknown product: {name}") from None
