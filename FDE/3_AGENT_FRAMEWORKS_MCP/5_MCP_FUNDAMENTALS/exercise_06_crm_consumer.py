"""Exercise 6: mock MCP server, tool catalog, and a two-step consumer flow."""

import json
import time
from dataclasses import dataclass, field
from typing import Any


MOCK_CUSTOMERS = {
    "c_4823": {
        "customer_id": "c_4823",
        "name": "Acme Subsidiary Inc",
        "tier": "pro",
        "mrr_usd": 1299,
        "open_tickets": 1,
    },
}
MOCK_TICKETS = {
    "c_4823": [
        {
            "ticket_id": "T9201",
            "status": "open",
            "subject": "Invoice question",
        }
    ],
}


@dataclass
class MockMCPServer:
    name: str = "acmecorp-crm"
    call_log: list[dict[str, Any]] = field(default_factory=list)

    def list_tools(self) -> list[dict[str, Any]]:
        customer_id_schema = {
            "type": "string",
            "pattern": "^c_[a-z0-9]+$",
        }
        return [
            {
                "name": "lookup_customer",
                "description": "Fetch an AcmeCorp customer record by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {"customer_id": customer_id_schema},
                    "required": ["customer_id"],
                },
            },
            {
                "name": "list_open_tickets",
                "description": "List open support tickets for a customer.",
                "input_schema": {
                    "type": "object",
                    "properties": {"customer_id": customer_id_schema},
                    "required": ["customer_id"],
                },
            },
        ]

    def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.call_log.append(
            {"name": name, "arguments": arguments, "at": time.time()}
        )
        customer_id = arguments.get("customer_id", "")

        if name == "lookup_customer":
            record = MOCK_CUSTOMERS.get(customer_id)
            if record is None:
                return {
                    "isError": True,
                    "content": [
                        {"type": "text", "text": f"not found: {customer_id}"}
                    ],
                }
            return {
                "isError": False,
                "content": [
                    {"type": "text", "text": json.dumps(record)}
                ],
            }

        if name == "list_open_tickets":
            tickets = [
                ticket
                for ticket in MOCK_TICKETS.get(customer_id, [])
                if ticket["status"] == "open"
            ]
            return {
                "isError": False,
                "content": [{"type": "text", "text": json.dumps(tickets)}],
            }

        return {
            "isError": True,
            "content": [{"type": "text", "text": f"unknown tool: {name}"}],
        }


def to_model_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Translate the mock MCP tool definition to a model-tool catalog shape."""
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["input_schema"],
    }


def main() -> None:
    server = MockMCPServer()
    catalog = [to_model_tool(tool) for tool in server.list_tools()]
    print("Tools advertised to the model:")
    for tool in catalog:
        print(f"- {tool['name']}: {tool['description']}")

    # Offline demonstration: simulate the model selecting each tool in sequence.
    customer_result = server.call_tool(
        "lookup_customer", {"customer_id": "c_4823"}
    )
    print("\nStep 1 - lookup_customer:")
    print(customer_result["content"][0]["text"])

    ticket_result = server.call_tool(
        "list_open_tickets", {"customer_id": "c_4823"}
    )
    print("\nStep 2 - list_open_tickets:")
    print(ticket_result["content"][0]["text"])

    print(f"\nServer call log contains {len(server.call_log)} calls:")
    for entry in server.call_log:
        print(f"- {entry['name']} {entry['arguments']}")


if __name__ == "__main__":
    main()
