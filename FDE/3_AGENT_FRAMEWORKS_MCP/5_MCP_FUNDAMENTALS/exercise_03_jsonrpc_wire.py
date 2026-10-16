"""Exercise 3: inspect the JSON-RPC envelopes for tools/list and tools/call."""

import json
from typing import Any


def show_envelope(label: str, envelope: dict[str, Any]) -> None:
    print(f"{label}:")
    print(json.dumps(envelope, indent=2))
    print()


def main() -> None:
    list_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
    list_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {
                    "name": "lookup_customer",
                    "description": "Look up an AcmeCorp customer by ID.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string"},
                        },
                        "required": ["customer_id"],
                    },
                }
            ]
        },
    }
    call_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "lookup_customer",
            "arguments": {"customer_id": "c_4823"},
        },
    }
    call_response = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "customer_id": "c_4823",
                            "name": "Acme Subsidiary",
                            "tier": "pro",
                            "mrr_usd": 1299,
                        }
                    ),
                }
            ],
            "isError": False,
        },
    }

    show_envelope("A. tools/list request (client to server)", list_request)
    show_envelope("B. tools/list response (server to client)", list_response)
    show_envelope("C. tools/call request (client to server)", call_request)
    show_envelope("D. tools/call response (server to client)", call_response)

    print("Correlation rule:")
    print(
        f"  list request id {list_request['id']} matches response id "
        f"{list_response['id']}."
    )
    print(
        f"  call request id {call_request['id']} matches response id "
        f"{call_response['id']}."
    )
    print("The tool name is params.name; its input is params.arguments.")

    stateless_changes = [
        "Requests are self-contained and do not require a session ID.",
        "Per-request metadata can travel in the message _meta field.",
        "Protocol discovery/negotiation is handled separately from tool calls.",
    ]
    print("\nStateless-protocol concepts in the lesson:")
    for item in stateless_changes:
        print(f"- {item}")


if __name__ == "__main__":
    main()
