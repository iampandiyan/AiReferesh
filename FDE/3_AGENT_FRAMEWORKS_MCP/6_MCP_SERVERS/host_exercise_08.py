"""Interactive host/client for Exercise 8's in-memory MCP server.

Run from this directory with:
    py host_exercise_08.py

Exercise 8 defines its FastMCP server in the same file as its pytest suite,
so this host connects to the imported server object in memory.
"""

import asyncio

from fastmcp import Client

from exercise_08_in_memory_tests import mcp


async def show_progress(
    progress: float,
    total: float | None,
    message: str | None,
) -> None:
    """Display progress notifications from batch_check_refunds."""
    if total:
        print(f"[Progress] {progress:g}/{total:g}", end="")
    else:
        print(f"[Progress] {progress:g}", end="")
    if message:
        print(f" - {message}", end="")
    print()


async def show_log(notification) -> None:
    """Display log notifications emitted by the batch tool."""
    print(f"[Server log] {notification.level}: {notification.data}")


async def main() -> None:
    async with Client(
        mcp,
        progress_handler=show_progress,
        log_handler=show_log,
    ) as client:
        tools = await client.list_tools()
        print("Connected to Exercise 8's in-memory MCP server.")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        while True:
            print(
                "\nChoose an operation:\n"
                "1. Look up a customer\n"
                "2. List a customer's orders\n"
                "3. Check one refund\n"
                "4. Check a batch of refunds\n"
                "5. Read customer context resource\n"
                "6. Render escalation prompt\n"
                "q. Quit"
            )
            choice = input("Choice: ").strip().lower()

            if choice == "q":
                break
            if choice == "1":
                customer_id = input("Customer ID: ").strip()
                result = await client.call_tool(
                    "get_customer",
                    {"customer_id": customer_id},
                )
                print("Tool response:", result.data)
            elif choice == "2":
                customer_id = input("Customer ID: ").strip()
                status = input(
                    "Status [pending/paid/pending_refund, blank for any]: "
                ).strip()
                limit_text = input("Maximum results [20]: ").strip()
                try:
                    limit = int(limit_text) if limit_text else 20
                except ValueError:
                    print("Enter a whole number for the result limit.")
                    continue

                arguments = {"customer_id": customer_id, "limit": limit}
                if status:
                    arguments["status"] = status
                result = await client.call_tool("list_orders", arguments)
                print("Tool response:", result.data)
            elif choice == "3":
                order_id = input("Order ID: ").strip()
                result = await client.call_tool(
                    "check_refund_eligibility",
                    {"order_id": order_id},
                )
                print("Tool response:", result.data)
            elif choice == "4":
                order_ids_text = input(
                    "Comma-separated order IDs: "
                ).strip()
                order_ids = [
                    order_id.strip()
                    for order_id in order_ids_text.split(",")
                    if order_id.strip()
                ]
                if not order_ids:
                    print("Enter at least one order ID.")
                    continue
                result = await client.call_tool(
                    "batch_check_refunds",
                    {"order_ids": order_ids},
                )
                print("Batch response:", result.data)
            elif choice == "5":
                customer_id = input("Customer ID: ").strip()
                uri = f"customer-context://customers/{customer_id}"
                result = await client.read_resource(uri)
                print("Resource response:", result)
            elif choice == "6":
                customer_id = input("Customer ID: ").strip()
                issue_summary = input("Issue summary: ").strip()
                result = await client.get_prompt(
                    "escalation_template",
                    {
                        "customer_id": customer_id,
                        "issue_summary": issue_summary,
                    },
                )
                print("Prompt response:", result)
            else:
                print("Choose 1-6 or q.")


if __name__ == "__main__":
    asyncio.run(main())
