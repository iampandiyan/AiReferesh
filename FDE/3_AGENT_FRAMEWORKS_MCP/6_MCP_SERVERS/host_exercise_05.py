"""A simple host/client for Exercise 5's MCP resource and prompt.

Run from this directory with:
    py host_exercise_05.py
"""

import asyncio
from pathlib import Path

from fastmcp import Client


SERVER_SCRIPT = Path(__file__).with_name("exercise_05_resource_prompt.py")


async def main() -> None:
    # The script path makes FastMCP launch the server and connect over stdio.
    async with Client(str(SERVER_SCRIPT)) as client:
        print("Connected to the Exercise 5 MCP server.")

        resources = await client.list_resources()
        print("\nResources available:")
        for resource in resources:
            print(f"- {resource.name}: {resource.uri}")

        prompts = await client.list_prompts()
        print("\nPrompts available:")
        for prompt in prompts:
            print(f"- {prompt.name}: {prompt.description}")

        while True:
            customer_id = input(
                "\nCustomer ID (c_001 or another ID; q to quit): "
            ).strip()
            if customer_id.lower() == "q":
                break
            if not customer_id:
                print("Please enter a customer ID.")
                continue

            resource_uri = f"customer-context://customers/{customer_id}"
            print(f"\nReading resource: {resource_uri}")
            resource_result = await client.read_resource(resource_uri)
            print("Resource response:")
            print(resource_result)

            issue_summary = input("Issue summary for the prompt: ").strip()
            if not issue_summary:
                issue_summary = "No issue summary provided"

            print("\nRendering escalation_template...")
            prompt_result = await client.get_prompt(
                "escalation_template",
                {
                    "customer_id": customer_id,
                    "issue_summary": issue_summary,
                },
            )
            print("Prompt response:")
            print(prompt_result)


if __name__ == "__main__":
    asyncio.run(main())
