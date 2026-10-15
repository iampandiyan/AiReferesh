"""Exercise 4: asynchronous batch tool with progress and audit logging."""

from fastmcp import Context, FastMCP

mcp = FastMCP(name="acmecorp-crm")
REFUND_WINDOW_DAYS = 30
POLICY_VERSION = "v2.3"

_ORDERS = {
    "o_4823": ("pending_refund", 21),
    "o_1200": ("pending_refund", 45),
    "o_5590": ("pending_refund", 3),
    "o_7001": ("paid", 5),
}


def _eligibility(order_id: str) -> dict:
    """Evaluate one order without raising for an unknown order or policy failure."""
    order = _ORDERS.get(order_id)
    if order is None:
        return {
            "eligible": False,
            "reason": "order not found in AcmeCorp CRM",
            "policy_version": POLICY_VERSION,
            "order_id": order_id,
            "error_code": "ORDER_NOT_FOUND",
        }

    status, age_days = order
    if status != "pending_refund":
        return {
            "eligible": False,
            "reason": f"order status is '{status}'; only pending_refund may be processed",
            "policy_version": POLICY_VERSION,
            "order_id": order_id,
            "error_code": "WRONG_STATUS",
        }
    if age_days > REFUND_WINDOW_DAYS:
        return {
            "eligible": False,
            "reason": (
                f"order placed {age_days} days ago; outside the "
                f"{REFUND_WINDOW_DAYS}-day window"
            ),
            "policy_version": POLICY_VERSION,
            "order_id": order_id,
            "error_code": "OUTSIDE_WINDOW",
        }
    return {
        "eligible": True,
        "reason": (
            f"within {REFUND_WINDOW_DAYS}-day window; "
            f"order placed {age_days} days ago"
        ),
        "policy_version": POLICY_VERSION,
        "order_id": order_id,
        "error_code": None,
    }


@mcp.tool()
async def batch_check_refunds(order_ids: list[str], ctx: Context) -> dict:
    """Check many refund requests, reporting progress and one audit log per order."""
    total = len(order_ids)
    await ctx.info(f"batch_check_refunds start: {total} orders")

    results = []
    eligible = 0
    for index, order_id in enumerate(order_ids, start=1):
        row = _eligibility(order_id)
        await ctx.report_progress(progress=index, total=total)
        await ctx.info(
            f"{order_id} -> eligible={row['eligible']} "
            f"error_code={row['error_code']}"
        )
        results.append(row)
        if row["eligible"]:
            eligible += 1

    await ctx.info(f"batch_check_refunds done: {eligible}/{total} eligible")
    return {"total": total, "eligible": eligible, "results": results}


if __name__ == "__main__":
    mcp.run()
