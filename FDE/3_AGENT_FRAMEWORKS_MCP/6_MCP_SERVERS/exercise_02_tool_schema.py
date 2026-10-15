"""Exercise 2: enum-constrained tool input and routing guidance."""

from enum import Enum

from fastmcp import FastMCP

mcp = FastMCP(name="acmecorp-crm")


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PENDING_REFUND = "pending_refund"


_ORDERS = {
    "o_4823": {
        "order_id": "o_4823",
        "customer_id": "c_001",
        "status": "pending_refund",
    },
    "o_5020": {
        "order_id": "o_5020",
        "customer_id": "c_002",
        "status": "paid",
    },
}


@mcp.tool()
def list_orders(
    customer_id: str,
    status: OrderStatus | None = None,
    limit: int = 20,
) -> list[dict]:
    """List a customer's orders, not to look up one customer.

    Filter by status when provided; results are capped at ``limit``.
    """
    limit = max(1, min(limit, 100))
    rows = [
        order
        for order in _ORDERS.values()
        if order["customer_id"] == customer_id
        and (status is None or order["status"] == status.value)
    ]
    return rows[:limit]


if __name__ == "__main__":
    mcp.run()
