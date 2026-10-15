"""Exercise 2: map child chunks to parent sections and deduplicate lookups.

Run with Python 3; no API key, embedding model, or external dependency is needed.

Lesson: index small children for precise retrieval, but preserve parent text for context.
Multiple retrieved children from one parent should return that parent only once; unknown
IDs should warn and be skipped instead of crashing the retrieval path.
"""

import re
from pprint import pprint


ARTICLE = """Synthetic consent policy.
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) Consent may be withdrawn at any time.
7(7) Withdrawal mechanisms shall meet the following requirements:
(a) shall be easy to use.
(b) shall be available in every language and modality needed by the data subject.
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.
"""


def build_parent_map(text: str) -> tuple[dict, dict]:
    sections = [part.strip() for part in re.split(r"(?=7\(\d+\))", text) if part.strip()]
    parents = {}
    child_to_parent = {}
    for parent_index, section in enumerate(sections):
        parent_id = f"parent_{parent_index}"
        child_sections = [part.strip() for part in re.split(r"(?=\([a-z]\)\s)", section) if part.strip()]
        child_rows = []
        for child_index, child_text in enumerate(child_sections):
            child_id = f"{parent_id}_child_{child_index}"
            child_rows.append({"id": child_id, "text": child_text})
            child_to_parent[child_id] = parent_id
        parents[parent_id] = {"parent_text": section, "children": child_rows}
    return parents, child_to_parent


def resolve_parents(child_ids: list[str], parent_map: dict, child_to_parent: dict) -> list[str]:
    resolved = []
    seen = set()
    for child_id in child_ids:
        parent_id = child_to_parent.get(child_id)
        if parent_id is None:
            print(f"[warn] unknown child id {child_id!r}; skipping")
            continue
        if parent_id not in seen:
            seen.add(parent_id)
            resolved.append(parent_map[parent_id]["parent_text"])
    return resolved


def main() -> None:
    parents, child_to_parent = build_parent_map(ARTICLE)
    print("parents:")
    pprint(parents)
    print("\nchild_to_parent:")
    pprint(child_to_parent)

    clause_parent = next(
        parent_id for parent_id, data in parents.items()
        if "7(7)" in data["parent_text"]
    )
    print("\nclause_parent:")
    pprint(clause_parent)

    children = parents[clause_parent]["children"]
    print("\nchildren:")
    pprint(children)

    demo_ids = [row["id"] for row in children[:2]] + ["does_not_exist"]
    print("\ndemo_ids:")
    pprint(demo_ids)

    resolved = resolve_parents(demo_ids, parents, child_to_parent)
    print("\nresolved:")
    pprint(resolved)
    print(f"Parents: {len(parents)}; child IDs: {len(child_to_parent)}")
    print(f"Resolved {len(resolved)} unique parent(s) from {len(demo_ids)} requested child IDs.")
    assert len(resolved) == 1
    print("Lesson: parent expansion restores heading/context without duplicating the same parent.")


if __name__ == "__main__":
    main()

"""
parents:
{'parent_0': {'children': [{'id': 'parent_0_child_0',
                            'text': 'Synthetic consent policy.'}],
              'parent_text': 'Synthetic consent policy.'},
 'parent_1': {'children': [{'id': 'parent_1_child_0',
                            'text': '7(1) Consent must be demonstrable.'}],
              'parent_text': '7(1) Consent must be demonstrable.'},
 'parent_2': {'children': [{'id': 'parent_2_child_0',
                            'text': '7(2) Written consent must be clear and '
                                    'accessible.'}],
              'parent_text': '7(2) Written consent must be clear and '
                             'accessible.'},
 'parent_3': {'children': [{'id': 'parent_3_child_0',
                            'text': '7(3) Consent may be withdrawn at any '
                                    'time.'}],
              'parent_text': '7(3) Consent may be withdrawn at any time.'},
 'parent_4': {'children': [{'id': 'parent_4_child_0',
                            'text': '7(7) Withdrawal mechanisms shall meet the '
                                    'following requirements:'},
                           {'id': 'parent_4_child_1',
                            'text': '(a) shall be easy to use.'},
                           {'id': 'parent_4_child_2',
                            'text': '(b) shall be available in every language '
                                    'and modality needed by the data subject.'},
                           {'id': 'parent_4_child_3',
                            'text': '(c) shall not require unnecessary '
                                    'personal data.'}],
              'parent_text': '7(7) Withdrawal mechanisms shall meet the '
                             'following requirements:\n'
                             '(a) shall be easy to use.\n'
                             '(b) shall be available in every language and '
                             'modality needed by the data subject.\n'
                             '(c) shall not require unnecessary personal '
                             'data.'},
 'parent_5': {'children': [{'id': 'parent_5_child_0',
                            'text': '7(8) Maintain a record of consent and '
                                    'withdrawal.'}],
              'parent_text': '7(8) Maintain a record of consent and '
                             'withdrawal.'}}

child_to_parent:
{'parent_0_child_0': 'parent_0',
 'parent_1_child_0': 'parent_1',
 'parent_2_child_0': 'parent_2',
 'parent_3_child_0': 'parent_3',
 'parent_4_child_0': 'parent_4',
 'parent_4_child_1': 'parent_4',
 'parent_4_child_2': 'parent_4',
 'parent_4_child_3': 'parent_4',
 'parent_5_child_0': 'parent_5'}

clause_parent:
'parent_4'

children:
[{'id': 'parent_4_child_0',
  'text': '7(7) Withdrawal mechanisms shall meet the following requirements:'},
 {'id': 'parent_4_child_1', 'text': '(a) shall be easy to use.'},
 {'id': 'parent_4_child_2',
  'text': '(b) shall be available in every language and modality needed by the '
          'data subject.'},
 {'id': 'parent_4_child_3',
  'text': '(c) shall not require unnecessary personal data.'}]

demo_ids:
['parent_4_child_0', 'parent_4_child_1', 'does_not_exist']
[warn] unknown child id 'does_not_exist'; skipping

resolved:
['7(7) Withdrawal mechanisms shall meet the following requirements:\n'
 '(a) shall be easy to use.\n'
 '(b) shall be available in every language and modality needed by the data '
 'subject.\n'
 '(c) shall not require unnecessary personal data.']
Parents: 6; child IDs: 9
Resolved 1 unique parent(s) from 3 requested child IDs.
Lesson: parent expansion restores heading/context without duplicating the same parent.
"""