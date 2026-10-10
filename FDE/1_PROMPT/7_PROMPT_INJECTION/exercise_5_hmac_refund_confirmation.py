"""Exercise 5: require an out-of-band HMAC token before a refund side effect.

Run with Python 3; no package or API key is needed. Set REFUND_HMAC_SECRET to a
long random secret before running for a persistent configured secret. If absent, this
demo creates a random per-process secret; it never prints or sends the secret to a model.

Lesson: untrusted model output must not mint authorization. Bind the signature to the
refund ID, amount, timestamp, and nonce; use constant-time comparison, expiry, and replay
protection. Production nonce storage must be durable and shared (for example, Redis).
"""

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass


SECRET = (os.environ.get("REFUND_HMAC_SECRET") or secrets.token_hex(32)).encode("utf-8")
TTL_SECONDS = 60
USED_NONCES: set[str] = set()


@dataclass
class RefundResult:
    ok: bool
    reason: str = ""
    refund_id: str = ""


def payload(refund_id: str, amount_usd: int, timestamp: int, nonce: str) -> bytes:
    return f"{refund_id}|{amount_usd}|{timestamp}|{nonce}".encode("utf-8")


def _mint_at(refund_id: str, amount_usd: int, timestamp: int) -> str:
    nonce = secrets.token_hex(8)
    signature = hmac.new(SECRET, payload(refund_id, amount_usd, timestamp, nonce), hashlib.sha256).hexdigest()
    return f"{timestamp}.{nonce}.{signature}"


def mint_confirm_token(refund_id: str, amount_usd: int) -> str:
    """Orchestrator-only: call only after a human/UI confirmation."""
    if not refund_id or type(amount_usd) is not int or amount_usd <= 0:
        raise ValueError("refund_id and a positive integer amount are required")
    return _mint_at(refund_id, amount_usd, int(time.time()))


def process_refund(refund_id: str, amount_usd: int, confirm_token: str) -> RefundResult:
    try:
        timestamp_text, nonce, signature = confirm_token.split(".", 2)
        timestamp = int(timestamp_text)
    except (AttributeError, TypeError, ValueError):
        return RefundResult(False, "malformed token")

    age = time.time() - timestamp
    if age < 0 or age > TTL_SECONDS:
        return RefundResult(False, f"token expired or not yet valid (TTL={TTL_SECONDS}s)")

    expected = hmac.new(SECRET, payload(refund_id, amount_usd, timestamp, nonce), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return RefundResult(False, "invalid HMAC signature")
    if nonce in USED_NONCES:
        return RefundResult(False, "nonce replay")

    USED_NONCES.add(nonce)
    return RefundResult(True, refund_id=refund_id)


def main() -> None:
    valid_token = mint_confirm_token("refund_TEST_001", 60)
    success = process_refund("refund_TEST_001", 60, valid_token)
    forged = f"{int(time.time())}.{secrets.token_hex(8)}.{'deadbeef' * 8}"
    forged_result = process_refund("refund_TEST_002", 60, forged)

    timestamp_text, nonce, signature = valid_token.split(".", 2)
    expired = f"{int(time.time()) - TTL_SECONDS - 1}.{nonce}.{signature}"
    expired_result = process_refund("refund_TEST_003", 60, expired)
    replay_result = process_refund("refund_TEST_001", 60, valid_token)

    amount_token = mint_confirm_token("refund_TEST_004", 60)
    amount_tamper = process_refund("refund_TEST_004", 600, amount_token)

    results = {
        "valid confirmation": success,
        "forged signature": forged_result,
        "expired token": expired_result,
        "replay": replay_result,
        "tampered amount": amount_tamper,
    }
    for label, result in results.items():
        print(f"{label:20s}: ok={result.ok}, reason={result.reason or 'accepted'}")

    assert success.ok
    assert not forged_result.ok and "signature" in forged_result.reason
    assert not expired_result.ok and "expired" in expired_result.reason
    assert not replay_result.ok and "replay" in replay_result.reason
    assert not amount_tamper.ok and "signature" in amount_tamper.reason
    print("Only a valid, fresh, unused, amount-bound orchestrator token is accepted.")


if __name__ == "__main__":
    main()