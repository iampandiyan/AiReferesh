"""
lab1_5_pgvector_langgraph_agent.py
====================================
LangGraph version of the Lab 1.5 multi-hop agent.

The graph makes the workflow explicit:

    resolve_bridge -> conditional route -> retrieve_target -> answer
                              \-> answer (when no bridge is found)

Retrieval remains a fixed PostgreSQL/pgvector tool. LangGraph coordinates the
state transitions; it does not generate SQL or execute arbitrary tools.
"""

import os
import re
from typing import Any, TypedDict

import psycopg2
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from pgvector.psycopg2 import register_vector
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

from lab1_5_common import build_corpus, generate_answer, get_chunks


class AgentState(TypedDict, total=False):
    question: str
    bridge_query: str
    target_query: str
    manager: str | None
    retrieved: list[tuple[str, float]]
    answer: str
    route: str


class LangGraphMultiHopAgent:
    TABLE_NAME = "lab1_5_langgraph_chunks"
    EMBED_DIM = 384

    def __init__(self, connection_config, embedding_model="all-MiniLM-L6-v2"):
        self.embed_model = SentenceTransformer(embedding_model)
        self.conn = psycopg2.connect(**connection_config)
        self.conn.autocommit = True
        register_vector(self.conn)
        self._ensure_schema()
        self.graph = self._build_graph()

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
        records = build_corpus(num_teams=num_teams, seed=seed)
        chunks, meta = get_chunks(records)
        record_pairs = [record for record in records for _ in (0, 1)]
        embeddings = self.embed_model.encode(
            chunks,
            normalize_embeddings=True,
        )
        rows = [
            (
                record["team"],
                record["manager"],
                metadata["role"],
                chunk,
                embedding,
            )
            for chunk, metadata, record, embedding in zip(
                chunks, meta, record_pairs, embeddings
            )
        ]

        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME};")
            if cur.fetchone()[0] == 0:
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

    def _retrieve(self, query, role=None, manager=None, top_k=1):
        query_embedding = self.embed_model.encode(
            [query],
            normalize_embeddings=True,
        )[0]
        filters = []
        parameters: list[Any] = [query_embedding]
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
            return [(text, float(score)) for text, score in cur.fetchall()]

    def _resolve_bridge(self, state: AgentState) -> AgentState:
        question = state["question"]
        bridge_query = f"Who manages the team mentioned in this question? {question}"
        bridge_results = self._retrieve(
            bridge_query,
            role="bridge_manager",
            top_k=1,
        )
        if not bridge_results:
            return {
                "bridge_query": bridge_query,
                "manager": None,
                "retrieved": [],
                "route": "answer",
            }

        manager_match = re.search(r"managed by (.+)\.", bridge_results[0][0])
        if not manager_match:
            return {
                "bridge_query": bridge_query,
                "manager": None,
                "retrieved": bridge_results,
                "route": "answer",
            }

        return {
            "bridge_query": bridge_query,
            "manager": manager_match.group(1),
            "retrieved": bridge_results,
            "route": "retrieve_target",
        }

    @staticmethod
    def _continue_or_answer(state: AgentState) -> str:
        return state.get("route", "answer")

    def _retrieve_target(self, state: AgentState) -> AgentState:
        manager = state["manager"]
        target_query = f"What is {manager}'s approval limit?"
        target_results = self._retrieve(
            target_query,
            role="target_limit",
            manager=manager,
            top_k=1,
        )
        return {
            "target_query": target_query,
            "retrieved": state.get("retrieved", []) + target_results,
            "route": "answer",
        }

    @staticmethod
    def _answer(state: AgentState) -> AgentState:
        retrieved = state.get("retrieved", [])
        if not retrieved:
            return {"answer": "Not found in the provided context."}
        context = "\n".join(text for text, _ in retrieved)
        return {"answer": generate_answer(context, state["question"])}

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("resolve_bridge", self._resolve_bridge)
        workflow.add_node("retrieve_target", self._retrieve_target)
        workflow.add_node("answer", self._answer)
        workflow.add_edge(START, "resolve_bridge")
        workflow.add_conditional_edges(
            "resolve_bridge",
            self._continue_or_answer,
            {
                "retrieve_target": "retrieve_target",
                "answer": "answer",
            },
        )
        workflow.add_edge("retrieve_target", "answer")
        workflow.add_edge("answer", END)
        return workflow.compile()

    def answer(self, question):
        return self.graph.invoke({"question": question})

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

    agent = LangGraphMultiHopAgent(pg_config)
    records = agent.load_demo_corpus()
    question = next(
        record["query"]
        for record in records
        if record["team"] == "Engineering North"
    )
    result = agent.answer(question)

    print("Bridge query:", result.get("bridge_query"))
    print("Resolved manager:", result.get("manager"))
    print("Target query:", result.get("target_query"))
    print("Retrieved:")
    for chunk_text, score in result.get("retrieved", []):
        print(f"[score={score:.4f}] {chunk_text}")
    print("Answer:", result.get("answer"))
    agent.close()
