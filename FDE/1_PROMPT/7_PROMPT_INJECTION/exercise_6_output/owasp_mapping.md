# OWASP LLM Top 10 Mapping (training reference)

| Category | Example defense layer |
|---|---|
| LLM01 Prompt Injection | Regex screening, untrusted-content spotlighting, and output validation |
| LLM02 Sensitive Information Disclosure | Minimize data and reject prompt leakage |
| LLM03 Supply Chain | Pin and review SDKs, model IDs, and prompt artifacts |
| LLM04 Data and Model Poisoning | Treat reviews and retrieved documents as untrusted data |
| LLM05 Improper Output Handling | Validate JSON schema before downstream use |
| LLM06 Excessive Agency | Keep authorization outside the model; require HMAC confirmation |
| LLM07 System Prompt Leakage | Check for long n-gram overlap and protect prompt storage |
| LLM08 Vector and Embedding Weaknesses | Apply trust labeling and input validation to retrieved content |
| LLM09 Misinformation | Use bounded schemas, evidence, and human review for consequential claims |
| LLM10 Unbounded Consumption | Set token, request, concurrency, and budget limits |

This table is an instructional mapping; verify current OWASP category names and guidance before using it as a compliance artifact.
