"""Exercise 2: keep orchestration fixed while selecting a Together model.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.
This standalone version is configured for openai/gpt-oss-120b on Together.

Behavior: the same calculator schema and tool loop from Exercise 1 are used.
Lesson: separating model configuration from tools/orchestration makes a model
swap a one-line change. This script runs the requested Together model only; a
provider-to-provider comparison requires credentials and endpoint configuration
for that other provider. Responses can vary in verbosity and tool-call behavior.
"""

import ast
import json
import operator
import os

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "Answer math questions with the calculator tool. Always use its result and "
    "show the result clearly."
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


def calculate(expression: str) -> float:
    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return float(OPERATORS[type(node.op)](visit(node.left), visit(node.right)))
        raise ValueError("Unsupported expression.")

    return visit(ast.parse(expression, mode="eval"))


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

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=500,
    )
    assistant_message = response.choices[0].message
    calls = assistant_message.tool_calls or []
    if not calls:
        raise RuntimeError("The model did not request the calculator tool.")
    messages.append(assistant_message.model_dump(exclude_none=True))
    for call in calls:
        if call.function.name != "calculator":
            raise RuntimeError(f"Unexpected tool requested: {call.function.name}")
        arguments = json.loads(call.function.arguments)
        try:
            result = {"result": calculate(arguments["expression"])}
        except (KeyError, SyntaxError, TypeError, ValueError, ZeroDivisionError) as error:
            result = {"error": str(error)}
        messages.append(
            {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
        )

    final = client.chat.completions.create(model=MODEL, messages=messages, max_tokens=300)
    print(f"Model: {MODEL}")
    print(final.choices[0].message.content or "No final response returned.")


if __name__ == "__main__":
    main()
