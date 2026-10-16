"""Exercise 4: choose between a tool, resource, or prompt."""

CAPABILITIES = {
    "Create a ticket for a customer": (
        "tool",
        "The model decides to invoke an action that creates a ticket.",
    ),
    "Customer history feed (last 20 interactions)": (
        "resource",
        "The host can attach read-only context without a tool-call round trip.",
    ),
    "User invokes /start-triage with a ticket ID": (
        "prompt",
        "The user selects a named workflow from the host UI.",
    ),
    "Issue a refund for an invoice": (
        "tool",
        "The model invokes an action that changes business state.",
    ),
    "Read-only compliance policy document": (
        "resource",
        "The host reads reference context for the model.",
    ),
}


def main() -> None:
    for capability, (primitive, reason) in CAPABILITIES.items():
        print(f"{primitive:8} | {capability}")
        print(f"         | {reason}")


if __name__ == "__main__":
    main()
