"""Exercise 8: compare MCP transports for a remote, multi-user CRM server."""

TRANSPORTS = {
    "stdio": {
        "spec_status": "Current local transport",
        "reach": "Local subprocess only",
        "load_balancer": "Not applicable",
        "resumable": "Not applicable",
        "cdn": "No",
        "verdict": "Reject for remote users",
    },
    "HTTP + SSE": {
        "spec_status": "Deprecated in the lesson scenario",
        "reach": "Remote",
        "load_balancer": "Sticky-session constraints",
        "resumable": "Limited",
        "cdn": "Poor fit",
        "verdict": "Reject for new deployment",
    },
    "Streamable HTTP": {
        "spec_status": "Current remote transport",
        "reach": "Remote",
        "load_balancer": "Supports stateless scaling",
        "resumable": "Supports event resumption",
        "cdn": "Single endpoint",
        "verdict": "Choose",
    },
}

CRITERIA = (
    "spec_status",
    "reach",
    "load_balancer",
    "resumable",
    "cdn",
    "verdict",
)


def main() -> None:
    print(f"{'Criterion':18} | " + " | ".join(f"{name:28}" for name in TRANSPORTS))
    print("-" * 118)
    for criterion in CRITERIA:
        values = " | ".join(
            f"{transport[criterion]:28}" for transport in TRANSPORTS.values()
        )
        print(f"{criterion:18} | {values}")

    print(
        "\nFor remote employees, the lesson recommends Streamable HTTP: "
        "it is a current network transport and supports scaling across "
        "server instances. stdio is local-only, while the lesson treats "
        "HTTP+SSE as deprecated."
    )


if __name__ == "__main__":
    main()
