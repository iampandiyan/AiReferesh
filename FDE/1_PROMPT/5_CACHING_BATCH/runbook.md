# Cache Invalidation Runbook

1. Compute and record the SHA-256 hash of the revised stable prompt; identify the policy revision.
2. Warm the new prefix with an approved synthetic canary request.
3. Verify provider-reported cache usage and confirm the cache-hit dashboard alert recovers above 0.7.
4. If cache behavior or output quality does not recover, disable the cache-dependent optimization, page the on-call owner, and investigate before routing production traffic back.
