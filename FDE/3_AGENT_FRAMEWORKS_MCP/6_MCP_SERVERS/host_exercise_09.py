"""Host application for Exercise 9.

Start the server in another terminal with:
    py exercise_09_package_entrypoint.py --http

Then run this host from this directory with:
    py host_exercise_09.py
"""

import asyncio

from client_exercise_09 import SERVER_URL, connect_to_server


async def main() -> None:
    # The host owns the user interaction; the client module handles MCP calls.
    async with connect_to_server() as client:
        tools = await client.list_tools()
        print(f"Connected to MCP server at {SERVER_URL}")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        while True:
            customer_id = input(
                "\nCustomer ID (c_001 or c_FAKE; q to quit): "
            ).strip()
            if customer_id.lower() == "q":
                break
            if not customer_id:
                print("Please enter a customer ID.")
                continue

            response = await client.get_customer(customer_id)
            print("Tool response:", response)


if __name__ == "__main__":
    asyncio.run(main())
