# Refund Tool Specification

All identifiers and records in the exercise are synthetic. Purpose values are required for PII-touching reads.

## lookup_payment
WHEN: First, to find payment state and customer reference. WHEN NOT: Never skip. PRE-REQS: payment_id and purpose (`refund_check`, `fraud_review`, or `onboarding`). SIDE EFFECTS: Read-only fixture lookup. GDPR purpose is recorded in the tool audit.

## check_refund_window
WHEN: After payment is confirmed captured. WHEN NOT: When payment is not captured. PRE-REQS: payment_id. SIDE EFFECTS: Read-only; independent of KYC lookup.

## verify_kyc
WHEN: After payment lookup. WHEN NOT: If already checked for this request. PRE-REQS: customer_id and GDPR purpose. SIDE EFFECTS: Read-only; independent of refund-window lookup.

## process_refund
WHEN: Only after captured status, open window, and verified KYC. WHEN NOT: If any precondition fails or payment has already been refunded. PRE-REQS: payment_id, amount, reason. SIDE EFFECTS: Mutates only the in-memory synthetic ledger; Python calculates `sha256(payment_id + reason)[:16]` and enforces all guards. Dry-run returns a synthetic refund ID and does not mutate the ledger.

## escalate_to_human
WHEN: A precondition fails or the result is uncertain. WHEN NOT: After a successful refund. PRE-REQS: A concise reason. SIDE EFFECTS: Returns a deterministic synthetic ticket.
