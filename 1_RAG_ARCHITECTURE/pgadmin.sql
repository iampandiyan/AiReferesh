CREATE EXTENSION vector;
SELECT extversion FROM pg_extension WHERE extname = 'vector';

CREATE TABLE test_items (
    id serial PRIMARY KEY,
    embedding vector(3)
);

INSERT INTO test_items (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

SELECT * FROM test_items ORDER BY embedding <-> '[1,2,4]' LIMIT 5;

DROP TABLE test_items;

SELECT to_tsvector('english', 'Article ERR-5012: Contact the support team using this reference code for resolution steps. Action required: restart the payment service, then retry.');
SELECT to_tsquery('english', 'err & 5012');
SELECT chunk_text FROM lab1_2_hybrid_chunks
WHERE ts_content @@ to_tsquery('english', 'err & 5012');

SELECT chunk_text FROM lab1_2_hybrid_chunks
WHERE ts_content @@ to_tsquery('english', 'err & -5012');

SELECT pid, state, query, query_start
FROM pg_stat_activity
WHERE datname = 'rag_labs' AND pid <> pg_backend_pid();



SELECT pg_terminate_backend(24680);
SELECT pg_terminate_backend(44264);


SELECT pid, state, query, query_start
FROM pg_stat_activity
WHERE datname = 'rag_labs' AND pid <> pg_backend_pid();

commit

