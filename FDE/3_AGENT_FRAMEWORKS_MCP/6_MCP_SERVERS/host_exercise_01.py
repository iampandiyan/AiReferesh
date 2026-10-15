"""A simple host/client for Exercise 1's stdio MCP server.

Run this file to launch the server as a subprocess, discover its tools,
and interactively call get_customer.
"""

import asyncio
from pathlib import Path

from fastmcp import Client


SERVER_SCRIPT = Path(__file__).with_name("exercise_01_baseline_server.py")


async def main() -> None:
    # Passing a server script path makes FastMCP launch it over stdio.
    async with Client(str(SERVER_SCRIPT)) as client:
        tools = await client.list_tools()
        print("Connected to the Exercise 1 MCP server.")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        print("\nEnter a customer ID to call get_customer (or q to quit).")
        while True:
            customer_id = input("Customer ID: ").strip()
            if customer_id.lower() == "q":
                break
            if not customer_id:
                print("Please enter a customer ID.")
                continue

            result = await client.call_tool(
                "get_customer",
                {"customer_id": customer_id},
            )
            print("Response:", result.data)


if __name__ == "__main__":
    asyncio.run(main())
