# Chunker Selection Memo

| Document type | Strategy | Rationale |
|---|---|---|
| PDF body | semantic + hierarchical | paragraph boundaries preserve clauses; parent expansion restores citations |
| numbered tables | row-as-chunk + replicated header | each retrieved row retains its column meaning |
| footnotes | attach to parent clause | an orphan footnote lacks its subject |
| annexures | header-based + hierarchical | preserve schedule and annex identifiers |
| lending memos | semantic | topic boundaries fit argumentative prose |
| chat transcripts | speaker-turn chunks + thread parent | preserve speaker attribution and conversation context |
