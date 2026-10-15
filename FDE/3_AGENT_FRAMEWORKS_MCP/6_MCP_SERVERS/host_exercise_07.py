"""A simple host/client for Exercise 7's observability middleware.

Run from this directory with:
    py host_exercise_07.py
"""

import asyncio
from pathlib import Path

from fastmcp import Client


SERVER_SCRIPT = Path(__file__).with_name("exercise_07_observability.py")


async def show_log(notification) -> None:
    """Print the structured log notification emitted by the server middleware."""
    print(f"\n[Server log notification] {notification}")


async def main() -> None:
    # The script path launches the server; log_handler receives ctx.info messages.
    async with Client(
        str(SERVER_SCRIPT),
        log_handler=show_log,
    ) as client:
        tools = await client.list_tools()
        print("Connected to the Exercise 7 MCP server.")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        print(
            "\nThe server middleware logs one JSON notification for each tool call."
        )
        print("The first call uses a known customer; the second uses an unknown ID.")

        for customer_id in ("c_001", "c_FAKE"):
            print(f"\nCalling get_customer(customer_id={customer_id!r})...")
            result = await client.call_tool(
                "get_customer",
                {"customer_id": customer_id},
            )
            print("Tool response:")
            print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
