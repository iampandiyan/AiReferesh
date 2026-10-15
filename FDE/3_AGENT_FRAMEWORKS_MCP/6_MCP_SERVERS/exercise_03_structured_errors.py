"""Exercise 3: reusable refund policy logic with structured error results."""

from datetime import datetime, timezone

_NOW = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
REFUND_WINDOW_DAYS = 30
POLICY_VERSION = "v2.3"

# order_id -> (status, days_since_placed)
_ORDERS = {
    "o_4823": ("pending_refund", 21),
    "o_1200": ("pending_refund", 45),
    "o_5590": ("pending_refund", 3),
    "o_7001": ("paid", 5),
}


def _eligibility(order_id: str) -> dict:
    """Return the same five-key result shape for every policy outcome."""
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


if __name__ == "__main__":
    for order_id in ("o_4823", "o_1200", "o_7001", "o_DOES_NOT_EXIST"):
        result = _eligibility(order_id)
        print(
            f"{order_id:18s} eligible={str(result['eligible']):5s} "
            f"error_code={result['error_code']}"
        )
