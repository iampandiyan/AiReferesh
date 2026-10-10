# Threat Model: Hardened Recommender

## Assets
Protect customer trust, private prompt/configuration data, merchant reputation, and any external action such as an order or refund. The model receives untrusted customer queries and may later receive untrusted review or tool-result content.

## Attack Families
Direct injection places an instruction override in the query. Indirect injection hides instructions in reviews or retrieved content. Tool injection places commands inside a tool result and tries to make the model invoke an action.

## Defense Layers
The regex filter catches known textual patterns before model use. Spotlighting wraps the query in `<untrusted_query>` and establishes an instruction hierarchy. The output validator rejects malformed JSON, task drift, and 12-token system-prompt overlap. Any future side-effectful action requires a short-lived, amount-bound HMAC confirmation minted by a trusted orchestrator after out-of-band approval.

## Residual Risk
Regex misses paraphrases, encoding, and novel languages; delimiters can be imitated inside content; models can return semantically wrong but schema-valid output; and a compromised orchestrator or leaked signing secret can defeat authorization. These controls reduce risk but do not prove safety. Minimize data, evaluate new attacks, rotate secrets, and require human review for consequential actions.

## Escalation
Reject suspicious or malformed outputs without forwarding them. Record a privacy-reviewed verdict and request ID, not raw sensitive content. Route repeated injection attempts or failed authorization checks to security/on-call review; pause side-effectful integrations during an incident.
