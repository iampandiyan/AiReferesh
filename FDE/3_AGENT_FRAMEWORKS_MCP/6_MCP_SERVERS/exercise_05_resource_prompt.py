"""Exercise 5: customer context resource and escalation prompt."""

from fastmcp import FastMCP

mcp = FastMCP(name="acmecorp-crm")

_CUSTOMERS = {
    "c_001": {
        "customer_id": "c_001",
        "name": "Aisha Khan",
        "tier": "Pro",
        "ltv_usd": 4820.0,
        "open_tickets": 2,
        "churn_risk": "low",
    },
}


@mcp.resource("customer-context://customers/{customer_id}")
def customer_context(customer_id: str) -> dict:
    """Return a compact customer context blob for agent working memory."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return {
            "customer_id": customer_id,
            "available": False,
            "reason": "customer not in CRM",
        }
    return {
        "customer_id": customer["customer_id"],
        "tier": customer["tier"],
        "ltv_usd": customer["ltv_usd"],
        "open_tickets": customer["open_tickets"],
        "churn_risk": customer["churn_risk"],
        "available": True,
    }


@mcp.prompt()
def escalation_template(customer_id: str, issue_summary: str) -> str:
    """Render a single escalation line; use a safe placeholder for an unknown ID."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return (
            f"Escalation for unknown customer '{customer_id}'. "
            f"Issue: {issue_summary}. Verify the ID first."
        )
    return (
        f"Customer {customer['customer_id']} ({customer['name']}, "
        f"{customer['tier']} tier, LTV ${customer['ltv_usd']:.2f}, "
        f"churn risk {customer['churn_risk']}) reports: {issue_summary}."
    )


if __name__ == "__main__":
    mcp.run()
