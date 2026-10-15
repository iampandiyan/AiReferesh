"""Exercise 8: a self-contained in-memory pytest suite for the MCP examples.

Run with ``pytest -q exercise_08_in_memory_tests.py`` or execute this file
directly after installing the lesson dependencies.
"""

from enum import Enum

import pytest
from fastmcp import Client, Context, FastMCP

mcp = FastMCP(name="acmecorp-crm")


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PENDING_REFUND = "pending_refund"


_CUSTOMERS = {
    "c_001": {"customer_id": "c_001", "name": "Aisha Khan", "tier": "Pro"},
}
_ORDERS = {
    "o_4823": ("pending_refund", 21, "c_001"),
    "o_1200": ("pending_refund", 45, "c_001"),
    "o_7001": ("paid", 5, "c_001"),
}


def _eligibility(order_id: str) -> dict:
    order = _ORDERS.get(order_id)
    if order is None:
        return {
            "eligible": False,
            "reason": "order not found in AcmeCorp CRM",
            "policy_version": "v2.3",
            "order_id": order_id,
            "error_code": "ORDER_NOT_FOUND",
        }
    status, age_days, _customer_id = order
    if status != "pending_refund":
        return {
            "eligible": False,
            "reason": "only pending_refund orders may be processed",
            "policy_version": "v2.3",
            "order_id": order_id,
            "error_code": "WRONG_STATUS",
        }
    if age_days > 30:
        return {
            "eligible": False,
            "reason": "outside the 30-day window",
            "policy_version": "v2.3",
            "order_id": order_id,
            "error_code": "OUTSIDE_WINDOW",
        }
    return {
        "eligible": True,
        "reason": "within the 30-day window",
        "policy_version": "v2.3",
        "order_id": order_id,
        "error_code": None,
    }


@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Look up an AcmeCorp customer by ID."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return {
            "error": True,
            "code": "CUSTOMER_NOT_FOUND",
            "customer_id": customer_id,
        }
    return customer


@mcp.tool()
def list_orders(
    customer_id: str,
    status: OrderStatus | None = None,
    limit: int = 20,
) -> list[dict]:
    """List a customer's orders, optionally filtered by status."""
    limit = max(1, min(limit, 100))
    return [
        {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": order_status,
        }
        for order_id, (order_status, _age_days, order_customer_id) in _ORDERS.items()
        if order_customer_id == customer_id
        and (status is None or order_status == status.value)
    ][:limit]


@mcp.tool()
def check_refund_eligibility(order_id: str) -> dict:
    """Check refund eligibility according to policy v2.3."""
    return _eligibility(order_id)


@mcp.tool()
async def batch_check_refunds(order_ids: list[str], ctx: Context) -> dict:
    """Check refund eligibility for a batch with progress and audit logs."""
    total = len(order_ids)
    await ctx.info(f"batch_check_refunds start: {total} orders")
    results = []
    eligible = 0
    for index, order_id in enumerate(order_ids, start=1):
        result = _eligibility(order_id)
        await ctx.report_progress(progress=index, total=total)
        await ctx.info(
            f"{order_id} -> eligible={result['eligible']} "
            f"error_code={result['error_code']}"
        )
        results.append(result)
        eligible += int(result["eligible"])
    await ctx.info(f"batch_check_refunds done: {eligible}/{total} eligible")
    return {"total": total, "eligible": eligible, "results": results}


@mcp.resource("customer-context://customers/{customer_id}")
def customer_context(customer_id: str) -> dict:
    """Return compact customer context or an unavailable response."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return {"customer_id": customer_id, "available": False}
    return {
        **customer,
        "ltv_usd": 4820.0,
        "open_tickets": 2,
        "churn_risk": "low",
        "available": True,
    }


@mcp.prompt()
def escalation_template(customer_id: str, issue_summary: str) -> str:
    """Render one customer escalation line."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return (
            f"Escalation for unknown customer '{customer_id}'. "
            f"Issue: {issue_summary}. Verify the ID first."
        )
    return (
        f"Customer {customer_id} ({customer['name']}, {customer['tier']} tier) "
        f"reports: {issue_summary}."
    )


@pytest.mark.asyncio
async def test_lists_tools_and_customer_happy_path():
    async with Client(mcp) as client:
        names = {tool.name for tool in await client.list_tools()}
        assert {
            "get_customer",
            "list_orders",
            "check_refund_eligibility",
            "batch_check_refunds",
        } <= names
        result = await client.call_tool("get_customer", {"customer_id": "c_001"})
        assert result.data["name"] == "Aisha Khan"


@pytest.mark.asyncio
async def test_unknown_customer_returns_structured_error():
    async with Client(mcp) as client:
        result = await client.call_tool("get_customer", {"customer_id": "c_missing"})
        assert result.data == {
            "error": True,
            "code": "CUSTOMER_NOT_FOUND",
            "customer_id": "c_missing",
        }


@pytest.mark.asyncio
async def test_refund_inside_window_is_eligible():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_refund_eligibility", {"order_id": "o_4823"}
        )
        assert result.data["eligible"] is True
        assert result.data["error_code"] is None


@pytest.mark.asyncio
async def test_refund_outside_window_is_not_eligible():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_refund_eligibility", {"order_id": "o_1200"}
        )
        assert result.data["eligible"] is False
        assert result.data["error_code"] == "OUTSIDE_WINDOW"


@pytest.mark.asyncio
async def test_wrong_order_status_is_structured():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_refund_eligibility", {"order_id": "o_7001"}
        )
        assert result.data["error_code"] == "WRONG_STATUS"


@pytest.mark.asyncio
async def test_unknown_order_returns_structured_error_not_exception():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_refund_eligibility", {"order_id": "o_DOES_NOT_EXIST"}
        )
        assert result.data["eligible"] is False
        assert result.data["error_code"] == "ORDER_NOT_FOUND"


@pytest.mark.asyncio
async def test_batch_progress_and_results():
    progress_events = []

    async def on_progress(progress, total, message):
        progress_events.append((progress, total))

    async with Client(mcp, progress_handler=on_progress) as client:
        result = await client.call_tool(
            "batch_check_refunds",
            {"order_ids": ["o_4823", "o_1200", "o_DOES_NOT_EXIST"]},
        )

    assert progress_events == [(1, 3), (2, 3), (3, 3)]
    assert result.data["total"] == 3
    assert result.data["eligible"] == 1
    assert result.data["results"][2]["error_code"] == "ORDER_NOT_FOUND"


@pytest.mark.asyncio
async def test_customer_resource():
    async with Client(mcp) as client:
        result = await client.read_resource("customer-context://customers/c_001")
        assert "Aisha Khan" in str(result)


@pytest.mark.asyncio
async def test_escalation_prompt():
    async with Client(mcp) as client:
        result = await client.get_prompt(
            "escalation_template",
            {"customer_id": "c_001", "issue_summary": "refund delay"},
        )
        assert "refund delay" in str(result)


@pytest.mark.asyncio
async def test_invalid_schema_input_is_rejected():
    async with Client(mcp) as client:
        with pytest.raises(Exception):
            await client.call_tool(
                "list_orders",
                {"customer_id": "c_001", "limit": "not-an-int"},
            )


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
