"""
lab1_5_pgvector_auto_agent.py
================================
A small constrained agent for the Lab 1.5 corpus. It decides whether a
question needs the team -> manager -> approval-limit plan, executes the
necessary pgvector searches, and uses one final LLM call for the answer.

The planner is deliberately deterministic: supported intents are selected
from validated question patterns, while unknown questions use direct search.
"""

import os
import json
import re

import psycopg2
from pgvector.psycopg2 import register_vector
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from lab1_5_common import (
    build_corpus,
    client,
    generate_answer,
    get_chunks,
    MODEL,
)


class AutoMultiHopAgent:
    """Plan and execute bounded retrieval workflows over pgvector."""

    TABLE_NAME = "lab1_5_auto_agent_chunks"
    EMBED_DIM = 384

    def __init__(self, connection_config, embedding_model="all-MiniLM-L6-v2"):
        self.embed_model = SentenceTransformer(embedding_model)
        self.conn = psycopg2.connect(**connection_config)
        self.conn.autocommit = True
        register_vector(self.conn)
        self._ensure_schema()

    def _ensure_schema(self):
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id bigserial PRIMARY KEY,
                    team text NOT NULL,
                    manager text NOT NULL,
                    role text NOT NULL,
                    chunk_text text NOT NULL,
                    embedding vector({self.EMBED_DIM}) NOT NULL
                );
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.TABLE_NAME}_role_idx
                ON {self.TABLE_NAME} (role);
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.TABLE_NAME}_embedding_hnsw
                ON {self.TABLE_NAME}
                USING hnsw (embedding vector_cosine_ops);
            """)

    def load_demo_corpus(self, num_teams=50, seed=42):
        """Load the deterministic lab corpus once for demonstration."""
        records = build_corpus(num_teams=num_teams, seed=seed)
        chunks, meta = get_chunks(records)
        rows = []
        for chunk_text, metadata, record in zip(
            chunks,
            meta,
            [record for record in records for _ in (0, 1)],
        ):
            rows.append((
                record["team"],
                record["manager"],
                metadata["role"],
                chunk_text,
                None,
            ))

        embeddings = self.embed_model.encode(
            chunks,
            normalize_embeddings=True,
        )
        rows = [row[:-1] + (embedding,) for row, embedding in zip(rows, embeddings)]

        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME};")
            if cur.fetchone()[0] != 0:
                return records
            execute_values(
                cur,
                f"""
                INSERT INTO {self.TABLE_NAME}
                    (team, manager, role, chunk_text, embedding)
                VALUES %s
                """,
                rows,
                page_size=500,
            )
        return records

    def _retrieve(self, query, team=None, role=None, manager=None, top_k=1):
        query_embedding = self.embed_model.encode(
            [query],
            normalize_embeddings=True,
        )[0]
        filters = []
        parameters = [query_embedding]
        if team is not None:
            filters.append("team = %s")
            parameters.append(team)
        if role is not None:
            filters.append("role = %s")
            parameters.append(role)
        if manager is not None:
            filters.append("manager = %s")
            parameters.append(manager)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        parameters.extend([query_embedding, top_k])

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
                FROM {self.TABLE_NAME}
                {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                parameters,
            )
            return cur.fetchall()

    @staticmethod
    def _direct_plan():
        return {"intent": "direct", "team": None}

    def _plan(self, question):
        planner_prompt = f"""Classify this question for a retrieval agent.
Return JSON only, with exactly these fields:
{{"intent":"manager_approval_limit"|"direct","team":string|null}}

Use manager_approval_limit when the answer requires finding a team's manager
first and then finding that manager's approval limit. Extract the team name
from the question. Use direct for every other question.

QUESTION:
{question}
"""
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": planner_prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content.strip()
            plan = json.loads(content)
        except (json.JSONDecodeError, AttributeError, IndexError, TypeError):
            return self._direct_plan()

        if plan.get("intent") == "direct":
            return self._direct_plan()
        if plan.get("intent") != "manager_approval_limit":
            return self._direct_plan()
        if not isinstance(plan.get("team"), str) or not plan["team"].strip():
            return self._direct_plan()
        return {
            "intent": "manager_approval_limit",
            "team": plan["team"].strip(),
        }

    def answer(self, question):
        plan = self._plan(question)
        retrieved = []

        if plan["intent"] == "manager_approval_limit":
            hop1_query = f"Who manages the {plan['team']} team?"
            hop1_results = self._retrieve(
                hop1_query,
                team=plan["team"],
                role="bridge_manager",
                top_k=1,
            )
            if not hop1_results:
                return "Not found in the provided context.", plan, retrieved

            manager_match = re.search(
                r"managed by (.+)\.",
                hop1_results[0][0],
            )
            if not manager_match:
                return "Not found in the provided context.", plan, hop1_results

            manager = manager_match.group(1)
            hop2_query = f"What is {manager}'s approval limit?"
            hop2_results = self._retrieve(
                hop2_query,
                role="target_limit",
                manager=manager,
                top_k=1,
            )
            retrieved = hop1_results + hop2_results
        else:
            retrieved = self._retrieve(question, top_k=3)

        if not retrieved:
            return "Not found in the provided context.", plan, retrieved

        context = "\n".join(chunk_text for chunk_text, _ in retrieved)
        return generate_answer(context, question), plan, retrieved

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    load_dotenv()
    pg_config = {
        "host": os.environ.get("PG_HOST", "localhost"),
        "port": os.environ.get("PG_PORT", "5432"),
        "dbname": os.environ.get("PG_DB", "rag_labs"),
        "user": os.environ.get("PG_USER", "postgres"),
        "password": os.environ.get("PG_PASSWORD"),
    }

    agent = AutoMultiHopAgent(pg_config)
    records = agent.load_demo_corpus()
    question = next(
        record["query"]
        for record in records
        if record["team"] == "Engineering North"
    )
    answer, plan, retrieved = agent.answer(question)

    print("Plan:", plan)
    print("Retrieved:")
    for chunk_text, score in retrieved:
        print(f"[score={score:.4f}] {chunk_text}")
    print("Answer:", answer)
    agent.close()
