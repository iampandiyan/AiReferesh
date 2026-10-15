"""A simple host/client for Exercise 2's stdio MCP server.

Run from this directory with:
    py host_exercise_02.py
"""

import asyncio
from pathlib import Path

from fastmcp import Client


SERVER_SCRIPT = Path(__file__).with_name("exercise_02_tool_schema.py")
VALID_STATUSES = {"pending", "paid", "pending_refund"}


async def main() -> None:
    # The script path makes FastMCP launch the server and connect over stdio.
    async with Client(str(SERVER_SCRIPT)) as client:
        tools = await client.list_tools()
        print("Connected to the Exercise 2 MCP server.")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        print("\nEnter order search parameters (or q for customer ID to quit).")
        while True:
            customer_id = input("Customer ID: ").strip()
            if customer_id.lower() == "q":
                break
            if not customer_id:
                print("Please enter a customer ID.")
                continue

            status_input = input(
                "Status [pending/paid/pending_refund, blank for any]: "
            ).strip()
            if status_input and status_input not in VALID_STATUSES:
                print("Choose pending, paid, pending_refund, or leave it blank.")
                continue

            limit_input = input("Maximum results [20]: ").strip()
            try:
                limit = int(limit_input) if limit_input else 20
            except ValueError:
                print("Enter a whole number for the result limit.")
                continue

            arguments = {"customer_id": customer_id, "limit": limit}
            if status_input:
                arguments["status"] = status_input

            result = await client.call_tool("list_orders", arguments)
            print("Response:", result.data)


if __name__ == "__main__":
    asyncio.run(main())
