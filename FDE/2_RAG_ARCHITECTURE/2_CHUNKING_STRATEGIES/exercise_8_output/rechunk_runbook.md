# Re-chunk Migration Runbook

1. **Dual-write:** stamp new chunks with `v2-semantic-hier` and write old/new indexes for a limited canary.
2. **Backfill:** process historical documents in bounded batches; track failures and verify table-row headers.
3. **Shadow-read:** compare faithfulness, retrieval latency, and error rates without changing user-visible answers.
4. **Cutover:** switch reads only after the promotion gate is met and owners approve.
5. **Rollback:** point reads to the prior index/version, stop new writes if needed, and preserve both indexes until reconciliation.

Raw re-embed cost not calculated; set EMBEDDING_USD_PER_MILLION to a verified current rate.
