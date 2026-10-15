"""Explore calling Exercise 1's MCP tool with an in-memory MCP client.

Run from this directory with:
    py call_exercise_01.py

Change CUSTOMER_ID below to try a known or unknown customer.
"""

import asyncio

from fastmcp import Client

from exercise_01_baseline_server import mcp


CUSTOMER_ID = "c_001"


async def main() -> None:
    # Client(mcp) connects to the server in memory; no separate process is needed.
    async with Client(mcp) as client:
        # Discover the tools the server makes available to an MCP client.
        tools = await client.list_tools()
        print("Tools provided by the server:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        # Call the tool by name. Arguments are passed as a dictionary.
        print(f"\nCalling get_customer with customer_id={CUSTOMER_ID!r}")
        result = await client.call_tool(
            "get_customer",
            {"customer_id": CUSTOMER_ID},
        )

        # Print the data returned by the tool. Try c_001, then c_FAKE.
        print("Tool response:")
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
