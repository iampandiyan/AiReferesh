"""Exercise 6: additive schema changes and semantic versioning."""

from enum import Enum

from fastmcp import FastMCP

SEMVER_RULES = {
    "add a new tool": ("minor", "additive - old clients keep working"),
    "add an optional argument": (
        "minor",
        "additive - omitting it is unchanged behaviour",
    ),
    "rename a required argument": (
        "major",
        "breaking - old callers hit InvalidParams",
    ),
    "remove a tool": ("major", "breaking - callers of that tool now fail"),
}


class CustomerTier(str, Enum):
    FREE = "Free"
    PRO = "Pro"
    BUSINESS = "Business"
    ENTERPRISE = "Enterprise"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PENDING_REFUND = "pending_refund"


mcp = FastMCP(
    name="acmecorp-crm",
    version="2.1.0",
    instructions=(
        "AcmeCorp CRM v2.1.0 adds an optional tier filter to list_orders."
    ),
)

_ORDERS = [
    {
        "order_id": "o_4823",
        "customer_id": "c_001",
        "status": "pending_refund",
        "tier": "Pro",
    },
    {
        "order_id": "o_5020",
        "customer_id": "c_002",
        "status": "paid",
        "tier": "Business",
    },
]


@mcp.tool()
def list_orders(
    customer_id: str,
    status: OrderStatus | None = None,
    tier: CustomerTier | None = None,
    limit: int = 20,
) -> list[dict]:
    """List customer orders; the optional tier filter is new in version 2.1.0."""
    limit = max(1, min(limit, 100))
    rows = [
        order
        for order in _ORDERS
        if order["customer_id"] == customer_id
        and (status is None or order["status"] == status.value)
        and (tier is None or order["tier"] == tier.value)
    ]
    return rows[:limit]


if __name__ == "__main__":
    for change, (bump, reason) in SEMVER_RULES.items():
        print(f"{change:27s} -> {bump:5s} ({reason})")
    mcp.run()
