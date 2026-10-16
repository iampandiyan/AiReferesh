"""Exercise 7: mitigations for four common remote MCP security threats.

These are design prompts and defensive mitigations, not a security audit.
"""

MITIGATIONS = {
    "Confused deputy": (
        "Propagate the end user's identity and enforce per-user authorization "
        "at the CRM tool boundary. Restrict tokens to the intended audience."
    ),
    "Token passthrough": (
        "Validate token issuer, signature, and audience on every request. "
        "Do not forward a client's token downstream; exchange it for a "
        "correctly scoped token."
    ),
    "Tool poisoning": (
        "Treat third-party tool descriptions and schemas as untrusted data. "
        "VET and allowlist servers, and require human review before enabling "
        "tools."
    ),
    "Rug pull": (
        "Pin server versions and record tool-catalog hashes. Require renewed "
        "human consent when a tool description or schema changes."
    ),
}


def main() -> None:
    for threat, mitigation in MITIGATIONS.items():
        print(f"[{threat}]")
        print(f"  Mitigation: {mitigation}\n")
    print(
        "Remote, multi-user deployments need authentication, authorization, "
        "catalog review, and change monitoring."
    )


if __name__ == "__main__":
    main()
