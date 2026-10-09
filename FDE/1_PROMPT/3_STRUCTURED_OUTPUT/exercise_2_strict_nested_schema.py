"""Exercise 2: make every nested object strict-schema compatible.

This local Pydantic exercise needs no API key and has no dependency on another
exercise file. Install Pydantic with `python -m pip install pydantic` if needed.

Lesson: `extra='forbid'` must be configured on every nested model, not just the root.
Walk `$defs` and references to verify the emitted schema instead of assuming it is strict.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    swift: str = Field(pattern=r"^[A-Z]{6}[A-Z0-9]{2}$")
    city: str


class CustomerRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(pattern=r"^TC\d{8}$")
    branch: Branch


class EnrichedLoanIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: Literal["home", "car", "personal", "business"]
    amount_usd: int = Field(gt=0, le=10_000_000)
    customer: CustomerRef


def walk_objects(schema: dict, defs: dict, path: str = "$"):
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        yield from walk_objects(defs[ref_name], defs, path)
        return
    if schema.get("type") == "object":
        yield path, schema
        for key, value in schema.get("properties", {}).items():
            yield from walk_objects(value, defs, f"{path}.{key}")


def main() -> None:
    schema = EnrichedLoanIntent.model_json_schema()
    missing = [
        path
        for path, node in walk_objects(schema, schema.get("$defs", {}))
        if node.get("additionalProperties") is not False
    ]
    print("Objects missing additionalProperties: false:", missing)
    assert not missing, "Nested schema is not strict-mode safe."

    valid = EnrichedLoanIntent.model_validate(
        {
            "purpose": "home",
            "amount_usd": 6000,
            "customer": {
                "customer_id": "TC12345678",
                "branch": {"swift": "MERIUS33", "city": "Austin"},
            },
        }
    )
    print("Valid input still works:", valid.customer.branch.city)
    try:
        EnrichedLoanIntent.model_validate(
            {
                "purpose": "home",
                "amount_usd": 6000,
                "unexpected": True,
                "customer": {
                    "customer_id": "TC12345678",
                    "branch": {"swift": "MERIUS33", "city": "Austin"},
                },
            }
        )
    except ValidationError as error:
        print("Extra field rejected:", error.errors()[0]["type"])
    else:
        raise AssertionError("An extra field should be rejected.")


if __name__ == "__main__":
    main()