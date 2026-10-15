"""Exercise 7: per-tool latency, structured errors, and call counters."""

import json
import time
from collections import Counter

from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext

mcp = FastMCP(name="acmecorp-crm")
_TOOL_CALLS = Counter()
_ERROR_CODES = Counter()


class ObservabilityMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        started_at = time.perf_counter()
        result = await call_next(context)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 1)

        payload = result.structured_content or {}
        error_code = payload.get("error_code")
        _TOOL_CALLS[tool_name] += 1
        if error_code:
            _ERROR_CODES[error_code] += 1

        fastmcp_context = context.fastmcp_context
        if fastmcp_context is not None:
            await fastmcp_context.info(
                json.dumps(
                    {
                        "tool": tool_name,
                        "latency_ms": latency_ms,
                        "error_code": error_code,
                        "calls": _TOOL_CALLS[tool_name],
                    }
                )
            )
        return result


mcp.add_middleware(ObservabilityMiddleware())

_CUSTOMERS = {
    "c_001": {"customer_id": "c_001", "name": "Aisha Khan", "tier": "Pro"},
}


@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Look up a customer and return a structured error if not found."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return {
            "error": True,
            "code": "CUSTOMER_NOT_FOUND",
            "error_code": "CUSTOMER_NOT_FOUND",
            "customer_id": customer_id,
        }
    return {**customer, "error_code": None}


if __name__ == "__main__":
    mcp.run()
