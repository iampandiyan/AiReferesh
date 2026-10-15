"""Exercise 1: a minimal AcmeCorp customer lookup MCP server."""

from fastmcp import FastMCP

mcp = FastMCP(name="acmecorp-crm")

_CUSTOMERS = {
    "c_001": {"customer_id": "c_001", "name": "Aisha Khan", "tier": "Pro"},
}


@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Look up an AcmeCorp customer by ID.

    Returns the customer record, or a structured CUSTOMER_NOT_FOUND error.
    """
    record = _CUSTOMERS.get(customer_id)
    if record is None:
        return {
            "error": True,
            "code": "CUSTOMER_NOT_FOUND",
            "customer_id": customer_id,
        }
    return record


if __name__ == "__main__":
    mcp.run()
