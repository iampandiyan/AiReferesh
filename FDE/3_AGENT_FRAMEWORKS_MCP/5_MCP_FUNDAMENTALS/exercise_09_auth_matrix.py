"""Exercise 9: select an authentication pattern for each customer profile."""

AUTH_PROFILES = {
    "SaaS startup with individual user accounts": {
        "pattern": "OAuth 2.1 + PKCE",
        "reason": (
            "Supports per-user, revocable authorization; PKCE protects "
            "the authorization-code flow."
        ),
        "objection": (
            "Consent UX adds friction; that is a trade-off for user-level "
            "authorization and revocation."
        ),
    },
    "Zero-trust bank with no shared secrets": {
        "pattern": "mTLS",
        "reason": (
            "Client certificates authenticate the connection and fit "
            "zero-trust/service-mesh deployments."
        ),
        "objection": (
            "PKI and certificate rotation take effort; automate issuance "
            "and rotation as part of the deployment."
        ),
    },
    "Internal-only service with no end-user identity": {
        "pattern": "API key in Authorization: Bearer",
        "reason": (
            "A simple service credential can fit a restricted "
            "service-to-service integration."
        ),
        "objection": (
            "Keys need rotation and careful handling; never place them "
            "in URLs or source control."
        ),
    },
}


def main() -> None:
    for profile, details in AUTH_PROFILES.items():
        print(f"[{profile}]")
        print(f"  Recommended: {details['pattern']}")
        print(f"  Reason:      {details['reason']}")
        print(f"  Trade-off:   {details['objection']}\n")


if __name__ == "__main__":
    main()
