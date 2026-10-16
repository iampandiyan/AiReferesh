"""Exercise 5: distinguish sampling, roots, and elicitation."""

SCENARIOS = {
    "Bulk refund needs human confirmation of total and reason": (
        "elicitation",
        "The server pauses to collect structured human input before proceeding.",
    ),
    "Document indexer may read only approved AcmeCorp folders": (
        "roots",
        "The client declares the filesystem/URI boundaries available to the server.",
    ),
    "Triage server asks the host to draft a reply using its model": (
        "sampling",
        "The server asks the host to perform an LLM completion on its behalf.",
    ),
}


def main() -> None:
    for scenario, (primitive, reason) in SCENARIOS.items():
        print(f"{primitive:12} | {scenario}")
        print(f"{'':12} | {reason}")
    print(
        "\nThese are server-initiated interactions toward the client/host, "
        "unlike ordinary tool calls."
    )


if __name__ == "__main__":
    main()
