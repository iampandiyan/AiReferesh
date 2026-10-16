"""Exercise 2: discover a tool, then call it using an in-process mock server."""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InProcessServer:
    """Small mock server to demonstrate the tools/list and tools/call shapes."""

    name: str = "acmecorp-crm"
    call_log: list[dict[str, Any]] = field(default_factory=list)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "lookup_customer",
                "description": "Fetch an AcmeCorp customer by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                    },
                    "required": ["customer_id"],
                },
            }
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.call_log.append({"name": name, "arguments": arguments})
        if name != "lookup_customer":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"unknown tool: {name}"}],
            }

        record = {
            "customer_id": arguments["customer_id"],
            "name": "Acme Subsidiary Inc",
            "tier": "pro",
            "mrr_usd": 1299,
        }
        return {
            "isError": False,
            "content": [{"type": "text", "text": json.dumps(record)}],
        }


def main() -> None:
    server = InProcessServer()

    # Discovery: ask the server for its advertised tool catalog.
    tools = server.list_tools()
    catalog = [tool["name"] for tool in tools]
    print(f"Server advertises {len(catalog)} tool(s): {catalog}")
    for tool in tools:
        print(f"  {tool['name']}: {tool['description']}")

    # A client should call a tool the server actually advertised.
    tool_name = "lookup_customer"
    if tool_name not in catalog:
        print(f"Cannot call {tool_name!r}; it is not in the catalog.")
        return

    # Invocation: this mock represents the tools/call operation.
    result = server.call_tool(tool_name, {"customer_id": "c_4823"})
    print("isError:", result["isError"])
    print("content:", result["content"])
    print("Call log:", server.call_log)


if __name__ == "__main__":
    main()
