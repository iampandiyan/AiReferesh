# GenAI/AI-ML Cheatsheet — Topic 6 (Agentic AI & Orchestration Libraries)

**Companion to:** GenAI_Topic6_Agentic_AI_and_Orchestration.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

All examples below were executed for real — outputs shown are actual, not invented.

---

## `langchain_core.tools.tool` (decorator)

**Initialization:**
```python
from langchain_core.tools import tool

@tool
def square(x: int) -> int:
    """Returns the square of a number."""
    return x * x
```

**Top attributes/methods:**
| Attribute/Method | Explanation |
|---|---|
| `.name` | Tool name — defaults to the function name |
| `.description` | Pulled directly from the docstring — this is what an LLM reads to decide relevance |
| `.args` | Auto-generated JSON-schema-style argument spec, built from type hints |
| `.invoke(dict)` | Call the tool with a dict of arguments — this is the standard call interface an agent framework uses, not calling the plain Python function directly |

**Verified example:**
```python
print(square.name)          # square
print(square.description)   # Returns the square of a number.
print(square.args)          # {'x': {'title': 'X', 'type': 'integer'}}
print(square.invoke({"x": 6}))   # 36
```

---

## `langgraph.graph.StateGraph`

**Initialization:**
```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class MyState(TypedDict):
    val: int

graph = StateGraph(MyState)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.add_node(name, func)` | Register a node — `func` takes the state dict, returns a dict of KEYS TO UPDATE (not the full state) |
| `.set_entry_point(name)` | Declare which node runs first |
| `.add_edge(from_node, to_node)` | Unconditional connection — always go from A to B |
| `.add_conditional_edges(from_node, routing_func, mapping)` | Branch based on `routing_func`'s return value, looked up in `mapping` |
| `.compile()` | Finalize the graph into a runnable app |
| `app.invoke(initial_state)` | Run the graph from the entry point to `END`, returning the final state |
| `END` | Special sentinel node marking pipeline completion |

**Verified example:**
```python
def double_node(state: MyState) -> MyState:
    return {"val": state["val"] * 2}   # only returns the updated key

graph.add_node("double", double_node)
graph.set_entry_point("double")
graph.add_edge("double", END)

app = graph.compile()
print(app.invoke({"val": 5}))   # {'val': 10}
```

---

## Status
2 entries verified with real executed output. See the main Topic 6 doc for the full conditional-routing and multi-node pipeline examples built from these same primitives.
