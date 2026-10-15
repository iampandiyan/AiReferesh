"""Exercise 4: retrieve child clauses, expand parents, and measure faithfulness.

Run with Python 3; no API key or dependency is required. Retrieval uses a local hashed
bag-of-words vectorizer as a deterministic stand-in, not a trained semantic embedding model.

Lesson: a precise child hit may omit its governing section header. Parent expansion can
restore that context. Faithfulness here is an exact phrase-presence proxy on a small synthetic set.
"""

import hashlib
import math
import re
from pprint import pprint


ARTICLE = """Synthetic consent policy.
7(1) Where processing is based on consent, the controller must demonstrate consent.
7(2) Written consent must be distinguishable, intelligible, and use clear language.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Consider whether a contract is conditional on unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Consent withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and other notified languages, and with an accessible alternative for assistive technology users;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal.
"""
GOLDEN = [
    {"query": "In what languages must the consent withdrawal mechanism be available?", "clause": "(b) shall be available", "header": "7(7) Consent withdrawal mechanisms"},
    {"query": "Must withdrawing consent be as easy as giving it?", "clause": "(a) shall be as easy", "header": "7(7) Consent withdrawal mechanisms"},
    {"query": "What extra data may withdrawal require?", "clause": "(c) shall not require", "header": "7(7) Consent withdrawal mechanisms"},
    {"query": "What record must the controller maintain?", "clause": "maintain a record of consent", "header": "7(8)"},
    {"query": "Can consent be withdrawn at any time?", "clause": "right to withdraw consent at any time", "header": "7(3)"},
    {"query": "Is consent from a pre-ticked box valid?", "clause": "pre-ticked box is void", "header": "7(6)"},
]


def vectorize(text: str, dimensions: int = 256) -> list[float]:
    """Local feature hashing, not a pretrained semantic embedding."""
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def make_hierarchy(text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    sections = [part.strip() for part in re.split(r"(?=7\(\d+\))", text) if part.strip()]
    parents = {}
    children = []
    for section_index, section in enumerate(sections):
        parent_id = f"parent_{section_index}"
        parents[parent_id] = section
        for child_index, child in enumerate(re.split(r"(?=\([a-z]\)\s)", section)):
            child = child.strip()
            if child:
                children.append({"id": f"{parent_id}_{child_index}", "parent_id": parent_id, "text": child})
    return parents, children


def retrieve(query: str, children: list[dict], k: int = 5) -> list[dict]:
    query_vector = vectorize(query)
    scored = [(cosine(query_vector, vectorize(row["text"])), row) for row in children]
    return [row for _, row in sorted(scored, key=lambda item: item[0], reverse=True)[:k]]


def expand_parents(hits: list[dict], parents: dict[str, str], cap: int = 3) -> str:
    selected = []
    seen = set()
    for hit in hits:
        parent_id = hit["parent_id"]
        if parent_id not in seen:
            seen.add(parent_id)
            selected.append(parents[parent_id])
        if len(selected) >= cap:
            break
    return "\n".join(selected)


def faithful(context: str, case: dict) -> bool:
    return case["clause"].lower() in context.lower() and case["header"].lower() in context.lower()


def main() -> None:
    parents, children = make_hierarchy(ARTICLE)
    print("Parents:")
    pprint(parents)
    print("\nChildren:")
    pprint(children)

    baseline_hits = hierarchical_hits = 0
    for case in GOLDEN:
        hits = retrieve(case["query"], children)
        child_context = "\n".join(hit["text"] for hit in hits)
        parent_context = expand_parents(hits, parents)
        baseline_hits += faithful(child_context, case)
        hierarchical_hits += faithful(parent_context, case)
        print(f"\nQuery: {case['query']}")
        print("Retrieved child text:")
        for index, hit in enumerate(hits, 1):
            print(f"  [{index}] child={hit['id']} parent={hit['parent_id']}: {hit['text']}")
        print("Parent-expanded retrieved text:")
        print(parent_context)
        print(
            f"Faithful: children={faithful(child_context, case)}; "
            f"parent-expanded={faithful(parent_context, case)}"
        )
    total = len(GOLDEN)
    print(f"\nChildren-only faithfulness: {baseline_hits}/{total} ({baseline_hits / total:.1%})")
    print(f"Parent-expanded faithfulness: {hierarchical_hits}/{total} ({hierarchical_hits / total:.1%})")
    print("Vectorizer: local feature hashing, not OpenAI/Voyage embeddings. Results are a teaching proxy.")


if __name__ == "__main__":
    main()

"""
Parents:
{'parent_0': 'Synthetic consent policy.',
 'parent_1': '7(1) Where processing is based on consent, the controller must '
             'demonstrate consent.',
 'parent_2': '7(2) Written consent must be distinguishable, intelligible, and '
             'use clear language.',
 'parent_3': '7(3) The data subject has the right to withdraw consent at any '
             'time.',
 'parent_4': '7(4) Consider whether a contract is conditional on unnecessary '
             'consent.',
 'parent_5': '7(5) Consent shall be as easy to withdraw as to give.',
 'parent_6': '7(6) Consent obtained through fraud, coercion, or a pre-ticked '
             'box is void.',
 'parent_7': '7(7) Consent withdrawal mechanisms shall meet these '
             'requirements:\n'
             '(a) shall be as easy to use as the mechanism to give consent;\n'
             '(b) shall be available in every language in which consent was '
             'originally requested, including Spanish and other notified '
             'languages, and with an accessible alternative for assistive '
             'technology users;\n'
             '(c) shall not require additional personal data beyond what is '
             'necessary to authenticate the data subject.',
 'parent_8': '7(8) The controller shall maintain a record of consent and '
             'withdrawal.'}

Children:
[{'id': 'parent_0_0',
  'parent_id': 'parent_0',
  'text': 'Synthetic consent policy.'},
 {'id': 'parent_1_0',
  'parent_id': 'parent_1',
  'text': '7(1) Where processing is based on consent, the controller must '
          'demonstrate consent.'},
 {'id': 'parent_2_0',
  'parent_id': 'parent_2',
  'text': '7(2) Written consent must be distinguishable, intelligible, and use '
          'clear language.'},
 {'id': 'parent_3_0',
  'parent_id': 'parent_3',
  'text': '7(3) The data subject has the right to withdraw consent at any '
          'time.'},
 {'id': 'parent_4_0',
  'parent_id': 'parent_4',
  'text': '7(4) Consider whether a contract is conditional on unnecessary '
          'consent.'},
 {'id': 'parent_5_0',
  'parent_id': 'parent_5',
  'text': '7(5) Consent shall be as easy to withdraw as to give.'},
 {'id': 'parent_6_0',
  'parent_id': 'parent_6',
  'text': '7(6) Consent obtained through fraud, coercion, or a pre-ticked box '
          'is void.'},
 {'id': 'parent_7_0',
  'parent_id': 'parent_7',
  'text': '7(7) Consent withdrawal mechanisms shall meet these requirements:'},
 {'id': 'parent_7_1',
  'parent_id': 'parent_7',
  'text': '(a) shall be as easy to use as the mechanism to give consent;'},
 {'id': 'parent_7_2',
  'parent_id': 'parent_7',
  'text': '(b) shall be available in every language in which consent was '
          'originally requested, including Spanish and other notified '
          'languages, and with an accessible alternative for assistive '
          'technology users;'},
 {'id': 'parent_7_3',
  'parent_id': 'parent_7',
  'text': '(c) shall not require additional personal data beyond what is '
          'necessary to authenticate the data subject.'},
 {'id': 'parent_8_0',
  'parent_id': 'parent_8',
  'text': '7(8) The controller shall maintain a record of consent and '
          'withdrawal.'}]

Query: In what languages must the consent withdrawal mechanism be available?
Retrieved child text:
  [1] child=parent_2_0 parent=parent_2: 7(2) Written consent must be distinguishable, intelligible, and use clear language.
  [2] child=parent_7_1 parent=parent_7: (a) shall be as easy to use as the mechanism to give consent;
  [3] child=parent_8_0 parent=parent_8: 7(8) The controller shall maintain a record of consent and withdrawal.
  [4] child=parent_1_0 parent=parent_1: 7(1) Where processing is based on consent, the controller must demonstrate consent.
  [5] child=parent_5_0 parent=parent_5: 7(5) Consent shall be as easy to withdraw as to give.
Parent-expanded retrieved text:
7(2) Written consent must be distinguishable, intelligible, and use clear language.
7(7) Consent withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and other notified languages, and with an accessible alternative for assistive technology users;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal.
Faithful: children=False; parent-expanded=True

Query: Must withdrawing consent be as easy as giving it?
Retrieved child text:
  [1] child=parent_5_0 parent=parent_5: 7(5) Consent shall be as easy to withdraw as to give.
  [2] child=parent_7_1 parent=parent_7: (a) shall be as easy to use as the mechanism to give consent;
  [3] child=parent_2_0 parent=parent_2: 7(2) Written consent must be distinguishable, intelligible, and use clear language.
  [4] child=parent_6_0 parent=parent_6: 7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
  [5] child=parent_7_0 parent=parent_7: 7(7) Consent withdrawal mechanisms shall meet these requirements:
Parent-expanded retrieved text:
7(5) Consent shall be as easy to withdraw as to give.
7(7) Consent withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and other notified languages, and with an accessible alternative for assistive technology users;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(2) Written consent must be distinguishable, intelligible, and use clear language.
Faithful: children=True; parent-expanded=True

Query: What extra data may withdrawal require?
Retrieved child text:
  [1] child=parent_7_3 parent=parent_7: (c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
  [2] child=parent_2_0 parent=parent_2: 7(2) Written consent must be distinguishable, intelligible, and use clear language.
  [3] child=parent_7_0 parent=parent_7: 7(7) Consent withdrawal mechanisms shall meet these requirements:
  [4] child=parent_8_0 parent=parent_8: 7(8) The controller shall maintain a record of consent and withdrawal.
  [5] child=parent_5_0 parent=parent_5: 7(5) Consent shall be as easy to withdraw as to give.
Parent-expanded retrieved text:
7(7) Consent withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and other notified languages, and with an accessible alternative for assistive technology users;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(2) Written consent must be distinguishable, intelligible, and use clear language.
7(8) The controller shall maintain a record of consent and withdrawal.
Faithful: children=True; parent-expanded=True

Query: What record must the controller maintain?
Retrieved child text:
  [1] child=parent_8_0 parent=parent_8: 7(8) The controller shall maintain a record of consent and withdrawal.
  [2] child=parent_1_0 parent=parent_1: 7(1) Where processing is based on consent, the controller must demonstrate consent.
  [3] child=parent_3_0 parent=parent_3: 7(3) The data subject has the right to withdraw consent at any time.
  [4] child=parent_7_3 parent=parent_7: (c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
  [5] child=parent_2_0 parent=parent_2: 7(2) Written consent must be distinguishable, intelligible, and use clear language.
Parent-expanded retrieved text:
7(8) The controller shall maintain a record of consent and withdrawal.
7(1) Where processing is based on consent, the controller must demonstrate consent.
7(3) The data subject has the right to withdraw consent at any time.
Faithful: children=True; parent-expanded=True

Query: Can consent be withdrawn at any time?
Retrieved child text:
  [1] child=parent_2_0 parent=parent_2: 7(2) Written consent must be distinguishable, intelligible, and use clear language.
  [2] child=parent_3_0 parent=parent_3: 7(3) The data subject has the right to withdraw consent at any time.
  [3] child=parent_8_0 parent=parent_8: 7(8) The controller shall maintain a record of consent and withdrawal.
  [4] child=parent_7_0 parent=parent_7: 7(7) Consent withdrawal mechanisms shall meet these requirements:
  [5] child=parent_0_0 parent=parent_0: Synthetic consent policy.
Parent-expanded retrieved text:
7(2) Written consent must be distinguishable, intelligible, and use clear language.
7(3) The data subject has the right to withdraw consent at any time.
7(8) The controller shall maintain a record of consent and withdrawal.
Faithful: children=True; parent-expanded=True

Query: Is consent from a pre-ticked box valid?
Retrieved child text:
  [1] child=parent_6_0 parent=parent_6: 7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
  [2] child=parent_7_1 parent=parent_7: (a) shall be as easy to use as the mechanism to give consent;
  [3] child=parent_4_0 parent=parent_4: 7(4) Consider whether a contract is conditional on unnecessary consent.
  [4] child=parent_1_0 parent=parent_1: 7(1) Where processing is based on consent, the controller must demonstrate consent.
  [5] child=parent_5_0 parent=parent_5: 7(5) Consent shall be as easy to withdraw as to give.
Parent-expanded retrieved text:
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Consent withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and other notified languages, and with an accessible alternative for assistive technology users;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(4) Consider whether a contract is conditional on unnecessary consent.
Faithful: children=True; parent-expanded=True

Children-only faithfulness: 5/6 (83.3%)
Parent-expanded faithfulness: 6/6 (100.0%)
Vectorizer: local feature hashing, not OpenAI/Voyage embeddings. Results are a teaching proxy.
"""