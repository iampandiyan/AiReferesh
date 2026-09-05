# GenAI/AI-ML Principles — Topic 6: Agentic AI & Orchestration

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every graph, tool, and pipeline below is real, executed LangChain/LangGraph code — actual `StateGraph` compilation and execution, not descriptions. The one thing that can't run here is the actual LLM making decisions (no network access to Together AI) — those spots use clearly-labeled mock logic standing in for what an LLM would decide, with the real structural code around it unchanged from what you'd deploy.

---

## 1. Chains vs Agents — The Core Distinction

**A chain** is a fixed, predetermined sequence of steps — always A → B → C, regardless of input.
**An agent** dynamically decides which steps (tools) to use and in what order, based on reasoning about the current situation.

**Chain pattern (fixed sequence):**
```python
def retrieve_step(query):
    return f"[retrieved context for: {query}]"

def format_prompt_step(context):
    return f"Answer using this context: {context}"

def generate_step(prompt):
    # mock generation - a real chain would call an LLM here
    return f"[MOCK LLM ANSWER based on: {prompt}]"

def simple_chain(query):
    context = retrieve_step(query)
    prompt = format_prompt_step(context)
    answer = generate_step(prompt)
    return answer

print(simple_chain("What is chunking?"))
```
Output: `[MOCK LLM ANSWER based on: Answer using this context: [retrieved context for: What is chunking?]]`
Every call to `simple_chain` runs the exact same three steps in the exact same order — that's what makes it a chain, not an agent.

---

## 2. Tools — Real LangChain `@tool` Decorator

Tools are functions an agent can choose to call. The decorator automatically extracts a name, description, and argument schema from the function signature and docstring — this metadata is what an LLM actually reads to decide which tool fits a given task.

```python
from langchain_core.tools import tool

@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

@tool
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

print("tool name:", get_word_length.name)
print("tool description:", get_word_length.description)
print("tool args schema:", get_word_length.args)
print("direct invoke:", get_word_length.invoke({"word": "hallucination"}))
```
Output:
```
tool name: get_word_length
tool description: Returns the length of a word.
tool args schema: {'word': {'title': 'Word', 'type': 'string'}}
direct invoke: 13
```
**MCQ-relevant point:** the docstring isn't just documentation — it's actually sent to the LLM as part of the tool's description, so a vague or missing docstring genuinely degrades an agent's ability to pick the right tool. This is a real, production-relevant detail, not a style preference.

---

## 3. ReAct Pattern — Reasoning + Acting (Illustrated, Not a Live LLM)

The ReAct pattern interleaves reasoning ("what should I do next?") with acting (calling a tool), then observing the result before deciding the next step. Since no live LLM is available here, this mock illustrates the *structure* of that decision loop using simple keyword matching in place of an LLM's actual reasoning:

```python
tools_registry = {"get_word_length": get_word_length, "add_numbers": add_numbers}

def mock_agent_decide_tool(user_query):
    # A real agent uses an LLM to read the query + tool descriptions and decide.
    # This mock uses keyword matching only to show the STRUCTURE of that decision.
    if "length" in user_query.lower():
        return "get_word_length", {"word": user_query.split()[-1]}
    elif "add" in user_query.lower() or "+" in user_query:
        return "add_numbers", {"a": 3, "b": 4}
    return None, {}

query1 = "What is the length of supercalifragilisticexpialidocious"
tool_name, args = mock_agent_decide_tool(query1)
result = tools_registry[tool_name].invoke(args)
print(f"agent selected tool: {tool_name}, args: {args}, result: {result}")
```
Output: `agent selected tool: get_word_length, args: {'word': 'supercalifragilisticexpialidocious'}, result: 34`
The tool invocation itself (`tools_registry[tool_name].invoke(args)`) is real, executable LangChain code — only the *decision* of which tool to pick is mocked here in place of an LLM call.

---

## 4. LangGraph `StateGraph` — Real Graph Construction and Execution

This is genuinely compiled and executed LangGraph code — nodes, edges, conditional routing, and state passing, all real.

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    query: str
    retrieved: str
    confidence: float
    answer: str

def retrieve_node(state: AgentState) -> AgentState:
    query = state["query"]
    if "rag" in query.lower():
        return {"retrieved": "RAG grounds LLM answers in retrieved documents.", "confidence": 0.9}
    return {"retrieved": "", "confidence": 0.1}

def high_confidence_answer_node(state: AgentState) -> AgentState:
    return {"answer": f"Grounded answer: {state['retrieved']}"}

def low_confidence_fallback_node(state: AgentState) -> AgentState:
    return {"answer": "I don't have enough retrieved context to answer confidently."}

def route_by_confidence(state: AgentState) -> Literal["high_confidence_answer", "low_confidence_fallback"]:
    return "high_confidence_answer" if state["confidence"] >= 0.5 else "low_confidence_fallback"

graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("high_confidence_answer", high_confidence_answer_node)
graph.add_node("low_confidence_fallback", low_confidence_fallback_node)

graph.set_entry_point("retrieve")
graph.add_conditional_edges("retrieve", route_by_confidence, {
    "high_confidence_answer": "high_confidence_answer",
    "low_confidence_fallback": "low_confidence_fallback",
})
graph.add_edge("high_confidence_answer", END)
graph.add_edge("low_confidence_fallback", END)

app = graph.compile()
```

**Running the high-confidence path:**
```python
result1 = app.invoke({"query": "What is RAG?", "retrieved": "", "confidence": 0.0, "answer": ""})
print(result1)
```
Output: `{'query': 'What is RAG?', 'retrieved': 'RAG grounds LLM answers in retrieved documents.', 'confidence': 0.9, 'answer': 'Grounded answer: RAG grounds LLM answers in retrieved documents.'}`

**Running the low-confidence fallback path:**
```python
result2 = app.invoke({"query": "What is the weather on Mars?", "retrieved": "", "confidence": 0.0, "answer": ""})
print(result2)
```
Output: `{'query': 'What is the weather on Mars?', 'retrieved': '', 'confidence': 0.1, 'answer': "I don't have enough retrieved context to answer confidently."}`

Same compiled graph, two genuinely different execution paths — the conditional edge actually routed differently based on the `confidence` value each node produced.

---

## 5. Multi-Node Pipeline — Matches Your SWIFT MT599 LangGraph Project

This structure directly mirrors a multi-stage message-processing pipeline (parse → validate → route) — the same shape as your SWIFT MT599 LangGraph pipeline project:

```python
class PipelineState(TypedDict):
    raw_message: str
    parsed_fields: dict
    validation_status: str
    final_output: str

def parse_node(state: PipelineState) -> PipelineState:
    fields = {"sender": "BANKAABC", "receiver": "BANKXYZ", "amount": "1000.00"}
    return {"parsed_fields": fields}

def validate_node(state: PipelineState) -> PipelineState:
    fields = state["parsed_fields"]
    status = "VALID" if fields.get("sender") and fields.get("receiver") else "INVALID"
    return {"validation_status": status}

def route_by_validation(state: PipelineState) -> Literal["finalize", "reject"]:
    return "finalize" if state["validation_status"] == "VALID" else "reject"

def finalize_node(state: PipelineState) -> PipelineState:
    return {"final_output": f"Processed: {state['parsed_fields']}"}

def reject_node(state: PipelineState) -> PipelineState:
    return {"final_output": "Message rejected - validation failed"}

pipeline = StateGraph(PipelineState)
pipeline.add_node("parse", parse_node)
pipeline.add_node("validate", validate_node)
pipeline.add_node("finalize", finalize_node)
pipeline.add_node("reject", reject_node)

pipeline.set_entry_point("parse")
pipeline.add_edge("parse", "validate")
pipeline.add_conditional_edges("validate", route_by_validation, {
    "finalize": "finalize",
    "reject": "reject",
})
pipeline.add_edge("finalize", END)
pipeline.add_edge("reject", END)

pipeline_app = pipeline.compile()
result3 = pipeline_app.invoke({"raw_message": "MT599 mock", "parsed_fields": {}, "validation_status": "", "final_output": ""})
print(result3)
```
Output: `{'raw_message': 'MT599 mock', 'parsed_fields': {'sender': 'BANKAABC', 'receiver': 'BANKXYZ', 'amount': '1000.00'}, 'validation_status': 'VALID', 'final_output': "Processed: {'sender': 'BANKAABC', 'receiver': 'BANKXYZ', 'amount': '1000.00'}"}`

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"Agents and chains are the same thing, just different names"** — FALSE. Chains follow a fixed sequence; agents dynamically decide their own path based on reasoning about the current state (Section 1).
2. **"A tool's docstring is just for human documentation"** — FALSE, as Section 2 notes — it's actually part of what gets sent to the LLM to help it decide whether/how to call that tool.
3. **"LangGraph nodes must return the full state object"** — FALSE, as every node above shows — nodes typically return only the KEYS they're updating; LangGraph merges partial updates into the full state automatically.
4. **"Conditional edges require an LLM to decide the route"** — FALSE. As Section 4 and 5 show, the routing function can be pure Python logic (a confidence threshold, a validation check) — an LLM is one possible way to implement a routing decision, not a requirement of the pattern itself.
5. **"More agent autonomy is always better than a fixed chain"** — Not necessarily. Fixed chains are more predictable, easier to test, and cheaper (fewer LLM calls for "deciding what to do next") — agents earn their added complexity only when the task genuinely requires dynamic tool selection.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. What's the core structural difference between a chain and an agent? *(A chain follows a fixed step sequence every time; an agent dynamically decides its next action based on reasoning)*
2. In LangChain's `@tool` decorator, what two pieces of function metadata get exposed to an LLM for tool selection? *(The function's docstring as the description, and its type-hinted parameters as the argument schema)*
3. In a LangGraph node function, do you need to return the entire state dictionary? *(No — return only the keys being updated; LangGraph merges partial updates into the full state)*
4. What determines which branch a `add_conditional_edges` routing function takes? *(Whatever the routing function's return value is — matched against the mapping dict passed to `add_conditional_edges`, which can be pure logic, not necessarily an LLM decision)*
5. Why might a production system deliberately use a fixed chain instead of a more flexible agent? *(Predictability, testability, and lower cost — agents' dynamic decision-making adds LLM calls and unpredictability that isn't always worth the flexibility)*

---

## Status
Every LangGraph `StateGraph`, tool definition, and pipeline in this document is real, executed code — genuine graph compilation, conditional routing, and state merging, verified against actual output. Only the tool-selection *decision* itself (Sections 3) is mocked in place of an LLM call, since no live LLM is reachable from this sandbox — the surrounding structural code is identical to what you'd run in your actual environment.

Ready for the companion **Cheatsheet — Topic 6** or straight into **Topic 7: Fine-tuning vs Prompting vs RAG** whenever you want to continue.
