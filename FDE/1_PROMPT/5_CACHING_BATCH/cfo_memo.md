# CFO Memo: Prompt Cost and Workload Mix

Monthly savings are not estimated because current Together token rates were not configured.

This is an approximate extrapolation from 20 synthetic queries per mode using the configured model, openai/gpt-oss-120b. The estimate assumes 50,000 requests each day, a 30-day month, the measured prompt/output token mix, and a 70% stable-prefix realtime plus 30% concurrent overnight workload. Token rates must be supplied from the current Together rate card; reported cache tokens are priced at the normal input rate unless a separately verified cached-input rate is configured. Prices and provider behavior may change.

The comparison uses a short-prompt baseline and a longer stable RAG prefix; those prompts have different input sizes, so this is a workflow comparison, not an isolated test of a cache discount. Together usage metadata may or may not report cached tokens for this model. Concurrent submission is not a native batch API and receives no assumed batch discount.

Risks include policy revisions invalidating reusable context, cache availability changing by model or provider, and asynchronous processing missing deadlines for urgent support requests. Production measurement should use representative, approved data, tenant-isolated metrics, and a larger evaluation sample. Do not place customer identifiers or raw prompts in metric labels or long-lived logs. Before launch, verify current pricing, cache behavior, latency objectives, and data-retention rules. Consult the cache-invalidation runbook when the stable policy prefix changes.
