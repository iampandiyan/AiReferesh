"""Synthetic example module for function-boundary chunking."""


def estimate_monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """Return a fixed-payment estimate using a nominal annual interest rate."""
    if principal < 0 or months <= 0:
        raise ValueError("principal must be non-negative and months must be positive")
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def classify_review_window(age_days: int, configured_limit_days: int = 30) -> str:
    """Classify an example payment age without contacting a payment service."""
    if age_days < 0:
        raise ValueError("age_days cannot be negative")
    return "within_window" if age_days <= configured_limit_days else "needs_review"


class SyntheticPaymentRecord:
    """A tiny fixture object; IDs here are fake and are not real payment credentials."""

    def __init__(self, payment_id: str, amount_usd: int, status: str):
        self.payment_id = payment_id
        self.amount_usd = amount_usd
        self.status = status
