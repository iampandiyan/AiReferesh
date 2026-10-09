"""Exercise 2: improve a tool description and add a GDPR purpose parameter.

This is a local design exercise and makes no API calls. It uses only Python's standard
library, so no API key or SDK is required. It does not rely on another exercise file.

Lesson: describe when to call a tool, when not to call it, prerequisites, and side
effects. A specific contract reduces missed calls and unsafe or redundant calls; keep
descriptions concise because they are included in model context.
"""

import json


TOOL_BAD = {
    "name": "verify_kyc",
    "description": "Check KYC.",
    "input_schema": {
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"],
    },
}

TOOL_GOOD = {
    "name": "verify_kyc",
    "description": """WHEN TO CALL:
- After lookup_payment confirms status=captured and the request concerns a refund.
- Before process_refund; refund processing requires current KYC.

WHEN NOT TO CALL:
- If lookup_payment returned not_found.
- If this customer was already checked during this conversation.

PRE-REQUISITES:
- Use customer_id returned by lookup_payment; never send an SSN or passport number.
- Supply the permitted GDPR purpose.

SIDE EFFECTS:
- Read-only; records an audit event for the declared purpose.
- Returns kyc_state: verified, expired, or missing.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Synthetic cust_ identifier"},
            "purpose": {
                "type": "string",
                "enum": ["refund_check", "fraud_review", "onboarding"],
                "description": "Declared purpose for access",
            },
        },
        "required": ["customer_id", "purpose"],
        "additionalProperties": False,
    },
}


def main() -> None:
    description = TOOL_GOOD["description"]
    sections = ("WHEN TO CALL", "WHEN NOT TO CALL", "PRE-REQUISITES", "SIDE EFFECTS")
    assert all(section in description for section in sections)
    assert "lookup_payment" in description
    assert "not_found" in description and "already" in description
    assert TOOL_GOOD["input_schema"]["properties"]["purpose"]["enum"]
    approximate_tokens = len(description.split())
    assert approximate_tokens <= 250

    print("=== BEFORE ===")
    print(json.dumps(TOOL_BAD, indent=2))
    print("\n=== AFTER ===")
    print(json.dumps(TOOL_GOOD, indent=2))
    print(f"\nChecks passed; description is approximately {approximate_tokens} words.")
    print("Note: token count is approximate; word count is not a tokenizer.")


if __name__ == "__main__":
    main()

"""
=== BEFORE ===
{
  "name": "verify_kyc",
  "description": "Check KYC.",
  "input_schema": {
    "type": "object",
    "properties": {
      "customer_id": {
        "type": "string"
      }
    },
    "required": [
      "customer_id"
    ]
  }
}

=== AFTER ===
{
  "name": "verify_kyc",
  "description": "WHEN TO CALL:\n- After lookup_payment confirms status=captured and the request concerns a refund.\n- Before process_refund; refund processing requires current KYC.\n\nWHEN NOT TO CALL:\n- If lookup_payment returned not_found.\n- If this customer was already checked during this conversation.\n\nPRE-REQUISITES:\n- Use customer_id returned by lookup_payment; never send an SSN or passport number.\n- Supply the permitted GDPR purpose.\n\nSIDE EFFECTS:\n- Read-only; records an audit event for the declared purpose.\n- Returns kyc_state: verified, expired, or missing.",
  "input_schema": {
    "type": "object",
    "properties": {
      "customer_id": {
        "type": "string",
        "description": "Synthetic cust_ identifier"
      },
      "purpose": {
        "type": "string",
        "enum": [
          "refund_check",
          "fraud_review",
          "onboarding"
        ],
        "description": "Declared purpose for access"
      }
    },
    "required": [
      "customer_id",
      "purpose"
    ],
    "additionalProperties": false
  }
}

Checks passed; description is approximately 80 words.
Note: token count is approximate; word count is not a tokenizer.
"""