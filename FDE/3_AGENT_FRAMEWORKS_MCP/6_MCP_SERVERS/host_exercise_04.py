"""A simple host/client for Exercise 4's batch refund MCP tool.

Run from this directory with:
    py host_exercise_04.py
"""

import asyncio
from pathlib import Path

from fastmcp import Client


SERVER_SCRIPT = Path(__file__).with_name("exercise_04_context_batch.py")
SAMPLE_ORDER_IDS = "o_4823, o_1200, o_7001, o_DOES_NOT_EXIST"


async def show_progress(
    progress: float,
    total: float | None,
    message: str | None,
) -> None:
    """Display progress notifications sent by the batch tool."""
    if total:
        print(f"[Progress] {progress:g}/{total:g}", end="")
    else:
        print(f"[Progress] {progress:g}", end="")
    if message:
        print(f" - {message}", end="")
    print()


async def show_log(message) -> None:
    """Display log notifications sent by Context.info in the server."""
    print(f"[Server log] {message}")


async def main() -> None:
    # The script path makes FastMCP launch the server and connect over stdio.
    async with Client(
        str(SERVER_SCRIPT),
        progress_handler=show_progress,
        log_handler=show_log,
    ) as client:
        tools = await client.list_tools()
        print("Connected to the Exercise 4 MCP server.")
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        print(
            "\nEnter comma-separated order IDs. Press Enter to use the sample IDs:"
        )
        order_ids_input = input(f"[{SAMPLE_ORDER_IDS}]: ").strip()
        if order_ids_input:
            order_ids = [
                order_id.strip()
                for order_id in order_ids_input.split(",")
                if order_id.strip()
            ]
        else:
            order_ids = [
                order_id.strip() for order_id in SAMPLE_ORDER_IDS.split(",")
            ]

        if not order_ids:
            print("No order IDs were entered; nothing to call.")
            return

        print("\nCalling batch_check_refunds...")
        result = await client.call_tool(
            "batch_check_refunds",
            {"order_ids": order_ids},
        )
        print("\nBatch result:")
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
