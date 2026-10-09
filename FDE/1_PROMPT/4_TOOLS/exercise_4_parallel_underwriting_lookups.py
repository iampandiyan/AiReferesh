"""Exercise 4: compare sequential and parallel independent lookups.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Uses Together's async OpenAI-compatible client and gpt-oss-120b. IDs are synthetic
TEST values; tool stubs never contact a bank, tax authority, or credit bureau.

Lesson: independent reads can be requested and executed together. Parallel execution
reduces tool latency, but only when dependencies are modeled correctly and the model
actually requests multiple tools in the same turn. Model/API latency still varies.
"""

import asyncio
import json
import os
import time
from typing import Any

from openai import AsyncOpenAI


MODEL = "openai/gpt-oss-120b"
SYSTEM = "Gather credit, tax, and bank summary data, then give a brief underwriting summary."
QUERY = "Underwrite TEST case: ssn=SSN_TEST_001 tax_id=TAX_TEST_001 account=acct_TEST_77. Gather all three inputs."


async def lookup_credit(ssn: str) -> dict:
    await asyncio.sleep(0.4)
    return {"score": 782, "reference": ssn}


async def lookup_tax(tax_id: str) -> dict:
    await asyncio.sleep(0.4)
    return {"annual_revenue_usd": 15000, "reference": tax_id}


async def lookup_bank_statements(account_id: str) -> dict:
    await asyncio.sleep(0.4)
    return {"avg_monthly_balance_usd": 1000, "reference": account_id}


async def execute_tool(name: str, arguments: dict[str, Any]) -> dict:
    handlers = {
        "lookup_credit": lookup_credit,
        "lookup_tax": lookup_tax,
        "lookup_bank_statements": lookup_bank_statements,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    return await handler(**arguments)


def make_tools(parallel: bool) -> list[dict]:
    instruction = (
        "INDEPENDENT: call this in parallel with the other lookups."
        if parallel
        else "Sequential mode: call this tool alone and wait for its result before the next lookup."
    )
    return [
        {"type": "function", "function": {"name": "lookup_credit", "description": f"Read credit score. {instruction}", "parameters": {"type": "object", "properties": {"ssn": {"type": "string"}}, "required": ["ssn"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "lookup_tax", "description": f"Read tax revenue. {instruction}", "parameters": {"type": "object", "properties": {"tax_id": {"type": "string"}}, "required": ["tax_id"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "lookup_bank_statements", "description": f"Read bank balance. {instruction}", "parameters": {"type": "object", "properties": {"account_id": {"type": "string"}}, "required": ["account_id"], "additionalProperties": False}}},
    ]


async def run_once(client: AsyncOpenAI, parallel: bool) -> dict:
    tools = make_tools(parallel)
    messages = [{"role": "user", "content": QUERY}]
    started = time.perf_counter()
    max_tools_in_turn = 0
    for _ in range(6):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=parallel,
            max_tokens=600,
        )
        assistant_message = response.choices[0].message
        calls = assistant_message.tool_calls or []
        if not calls:
            return {
                "seconds": time.perf_counter() - started,
                "parallel_calls": max_tools_in_turn,
                "final": assistant_message.content or "",
            }
        max_tools_in_turn = max(max_tools_in_turn, len(calls))
        messages.append(assistant_message.model_dump(exclude_none=True))
        results = await asyncio.gather(*[
            execute_tool(call.function.name, json.loads(call.function.arguments))
            for call in calls
        ])
        messages.extend(
            {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            for call, result in zip(calls, results)
        )
    return {"seconds": time.perf_counter() - started, "parallel_calls": max_tools_in_turn, "final": "CAP_HIT"}


async def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = AsyncOpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    sequential = await run_once(client, parallel=False)
    parallel = await run_once(client, parallel=True)
    print(f"{'mode':12s} | wall-clock seconds | most tool calls in one turn")
    print("-" * 70)
    print(f"{'sequential':12s} | {sequential['seconds']:18.2f} | {sequential['parallel_calls']}")
    print(f"{'parallel':12s} | {parallel['seconds']:18.2f} | {parallel['parallel_calls']}")
    print(f"Speedup: {sequential['seconds'] / max(parallel['seconds'], 0.001):.2f}x")
    print("Parallel row makes multiple lookups in one turn:", parallel["parallel_calls"] >= 2)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
mode         | wall-clock seconds | most tool calls in one turn
----------------------------------------------------------------------
sequential   |               7.48 | 1
parallel     |               5.92 | 3
Speedup: 1.26x
Parallel row makes multiple lookups in one turn: True
"""