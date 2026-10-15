"""Exercise 9: stdio entry point for the packaged AcmeCorp MCP server.

Keep stdout reserved for MCP protocol frames; send application logs to stderr.
"""

import sys

from fastmcp import FastMCP

mcp = FastMCP(
    name="acmecorp-crm",
    version="2.1.0",
    instructions="AcmeCorp CRM support tools.",
)

_CUSTOMERS = {
    "c_001": {"customer_id": "c_001", "name": "Aisha Khan", "tier": "Pro"},
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


def main() -> None:
    """Run over stdio, or use ``--http`` for streamable HTTP deployment."""
    if "--http" in sys.argv:
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
