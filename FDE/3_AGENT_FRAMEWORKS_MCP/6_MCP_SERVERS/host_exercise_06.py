"""A simple host/client for Exercise 6's versioned MCP server.

Run from this directory with:
    py host_exercise_06.py
"""

import asyncio
from pathlib import Path

from fastmcp import Client


SERVER_SCRIPT = Path(__file__).with_name("exercise_06_versioning.py")
VALID_STATUSES = {"pending", "paid", "pending_refund"}
VALID_TIERS = {"Free", "Pro", "Business", "Enterprise"}


async def main() -> None:
    # The script path makes FastMCP launch the server and connect over stdio.
    async with Client(str(SERVER_SCRIPT)) as client:
        tools = await client.list_tools()
        print("Connected to the Exercise 6 MCP server.")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        customer_id = input("\nCustomer ID (c_001 or c_002): ").strip()
        if not customer_id:
            print("A customer ID is required.")
            return

        # Legacy-style request: only the required argument is sent.
        print("\nCalling list_orders without optional filters (older client shape)...")
        legacy_result = await client.call_tool(
            "list_orders",
            {"customer_id": customer_id},
        )
        print("Response without optional filters:")
        print(legacy_result.data)

        status = input(
            "\nOptional status [pending/paid/pending_refund, blank for any]: "
        ).strip()
        if status and status not in VALID_STATUSES:
            print("Invalid status; choose pending, paid, pending_refund, or blank.")
            return

        tier = input(
            "Optional tier [Free/Pro/Business/Enterprise, blank for any]: "
        ).strip()
        if tier and tier not in VALID_TIERS:
            print("Invalid tier; choose Free, Pro, Business, Enterprise, or blank.")
            return

        limit_input = input("Maximum results [20]: ").strip()
        try:
            limit = int(limit_input) if limit_input else 20
        except ValueError:
            print("Enter a whole number for the result limit.")
            return

        # Only include optional arguments when the user supplied them.
        arguments = {"customer_id": customer_id, "limit": limit}
        if status:
            arguments["status"] = status
        if tier:
            arguments["tier"] = tier

        print("\nCalling list_orders with the selected filters...")
        filtered_result = await client.call_tool("list_orders", arguments)
        print("Filtered response:")
        print(filtered_result.data)


if __name__ == "__main__":
    asyncio.run(main())
