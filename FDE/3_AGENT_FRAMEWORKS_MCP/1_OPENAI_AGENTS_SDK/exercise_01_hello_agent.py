"""Exercise 1: calculator tool round trip with a Together-hosted model.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.
The arithmetic tool uses a small AST allowlist rather than Python eval.

Behavior: the model requests the calculator, Python executes it, and the result
is sent back with the tool-call ID before the model writes its final answer.
Lesson: tools make exact operations deterministic; the model should not guess
the result of arithmetic it can delegate.
"""

import ast
import json
import operator
import os

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are a math helper. Use the calculator tool for arithmetic and explain "
    "the returned result. Do not calculate arithmetic mentally."
)
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a basic arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    }
]


def evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return float(OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right)))
    raise ValueError("Only numeric literals and +, -, *, / are supported.")


def calculator(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return evaluate(tree)


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    customer_message = "What is 23 * 47?"
    messages = [
        {"role": "system", "content": PROMPT_V1},
        {"role": "user", "content": customer_message},
    ]
    first = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=500,
    )
    assistant_message = first.choices[0].message
    calls = assistant_message.tool_calls or []
    if not calls:
        raise RuntimeError("The model did not request the calculator tool.")

    messages.append(assistant_message.model_dump(exclude_none=True))
    for call in calls:
        if call.function.name != "calculator":
            raise RuntimeError(f"Unexpected tool requested: {call.function.name}")
        arguments = json.loads(call.function.arguments)
        try:
            result = {"result": calculator(arguments["expression"])}
        except (KeyError, SyntaxError, TypeError, ValueError, ZeroDivisionError) as error:
            result = {"error": str(error)}
        messages.append(
            {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
        )

    final = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=300,
    )
    print(final.choices[0].message.content or "No final response returned.")


if __name__ == "__main__":
    main()
