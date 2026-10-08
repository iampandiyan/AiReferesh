# --- Keyless runnable guard (auto-inserted from the lesson HTML) --------------
# Learners WITH an ANTHROPIC_API_KEY / OPENAI_API_KEY hit the live model.
# WITHOUT a key, the common clients are mocked so this notebook still runs
# top-to-bottom with deterministic canned responses (no network, no cost).
import os
_HAS_ANTHROPIC = bool(os.environ.get("ANTHROPIC_API_KEY"))
_HAS_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))
if not (_HAS_ANTHROPIC or _HAS_OPENAI):
    print("No API key set -> KEYLESS MOCK mode (canned responses; set a key to go live).")
    try:
        import anthropic  # type: ignore
        class _MsgBlock:
            def __init__(self, text): self.text = text; self.type = "text"
        class _Msg:
            def __init__(self, text):
                self.content = [_MsgBlock(text)]
                self.stop_reason = "end_turn"
                self.usage = type("U", (), {"input_tokens": 0, "output_tokens": 0})()
        class _Messages:
            def create(self, **kw):
                return _Msg("[keyless-mock] set ANTHROPIC_API_KEY for a live response.")
        class _Anthropic:
            def __init__(self, *a, **k): self.messages = _Messages()
        anthropic.Anthropic = _Anthropic
        if hasattr(anthropic, "AsyncAnthropic"): anthropic.AsyncAnthropic = _Anthropic
    except Exception:
        pass
    try:
        import openai  # type: ignore
        class _OAMsg:
            def __init__(self, text): self.content = text
        class _OAChoice:
            def __init__(self, text): self.message = _OAMsg(text)
        class _OAResp:
            def __init__(self, text): self.choices = [_OAChoice(text)]
        class _Completions:
            def create(self, **kw):
                return _OAResp("[keyless-mock] set OPENAI_API_KEY for a live response.")
        class _Chat:
            def __init__(self): self.completions = _Completions()
        class _OpenAI:
            def __init__(self, *a, **k): self.chat = _Chat()
        openai.OpenAI = _OpenAI
        if hasattr(openai, "AsyncOpenAI"): openai.AsyncOpenAI = _OpenAI
    except Exception:
        pass
# ----------------------------------------------------------------------------
#Exercise 1 - From 1 line to 6 sections (code-mixed refund classifier)
# Worked solution - the 1-line prompt rewritten as 6 labelled sections.
PROMPT_V0 = "Classify this Stripe customer message as refund, not_refund, or escalate."

PROMPT_V1 = """
[SYSTEM]
You are a classifier for Stripe merchant-support inbound messages. US English spelling. Never invent customer details.

[ROLE]
Refund-intent triage agent. You only classify; you do not draft replies.

[CONTEXT]
Stripe merchants raise tickets in code-mixed, Spanish, and English. Refund windows are 5 business days from payment.

[INSTRUCTIONS]
1. Read the customer message.
2. Decide one of: refund, not_refund, escalate.
3. If the message mentions an unauthorized charge or fraud, always escalate.
4. Respond only with the JSON shape in [FORMAT]. No prose.

[EXAMPLES]
Input: "Oye me cobraron y el order se cancelo, quiero mi refund"
Output: {"intent": "refund", "confidence": 0.92}

Input: "Cuando llega el order?"
Output: {"intent": "not_refund", "confidence": 0.88}

Input: "Mi card tiene 4 unauthorized transactions"
Output: {"intent": "escalate", "confidence": 0.99}

[FORMAT]
Return ONLY: {"intent": "refund|not_refund|escalate", "confidence": 0.0-1.0}
"""

# Self-checks against the success criteria:
SECTIONS = ["[SYSTEM]", "[ROLE]", "[CONTEXT]", "[INSTRUCTIONS]", "[EXAMPLES]", "[FORMAT]"]
assert all(tag in PROMPT_V1 for tag in SECTIONS), "all 6 sections must be present"
# format spec lives only in [FORMAT], never duplicated in [INSTRUCTIONS]:
assert PROMPT_V1.count("refund|not_refund|escalate") == 1
# the fraud rule is the last-but-one numbered instruction (recency), not in [CONTEXT]:
ins = PROMPT_V1.split("[INSTRUCTIONS]")[1].split("[EXAMPLES]")[0]
assert "always escalate" in ins
print(PROMPT_V1)
print("OK - 6 sections present, no format leakage, fraud rule in [INSTRUCTIONS].")


#Exercise 2 - The buried instruction: find it, relocate it, end-anchor it
# Failure mode (one sentence): the language rule is buried in a paragraph of [CONTEXT]
# ~1500 tokens from the user message; on short code-mixed queries recency makes the model
# default to English because the rule sits too far from the user turn.

BROKEN = """
[SYSTEM]
You are a Stripe merchant-support agent.

[ROLE]
You answer merchant tickets about payments, refunds, KYC, and settlements.

[CONTEXT]
Stripe processes payments for 10M+ merchants. The platform supports
cards, bank transfers, and wallets. Settlement happens on T+2 by default.
Merchants often write in code-mixed mixing Spanish words with English. We must
respond in the same language and script the merchant used so the reply is
intelligible to non-English-comfortable merchants. KYC is mandatory under
regulator guidelines. Refund windows are 5 business days from payment time.

[INSTRUCTIONS]
1. Read the merchant message.
2. Identify the issue type.
3. Draft a 2-3 sentence reply.

[EXAMPLES]
Input: "Oye el settlement no llego ni despues de T+2"
Output: "Estamos revisando tu settlement, update en 2 horas."

[FORMAT]
Reply with 2-3 sentences only. No JSON.
"""

# FIXED: platform facts stay in [CONTEXT]; the language rule moves to [INSTRUCTIONS] item 4
# and is repeated as a one-line end-anchor right before [FORMAT]. Nothing else changes.
FIXED = """
[SYSTEM]
You are a Stripe merchant-support agent.

[ROLE]
You answer merchant tickets about payments, refunds, KYC, and settlements.

[CONTEXT]
Stripe processes payments for 10M+ merchants. The platform supports
cards, bank transfers, and wallets. Settlement happens on T+2 by default.
KYC is mandatory under regulator guidelines. Refund windows are 5 business days from payment time.

[INSTRUCTIONS]
1. Read the merchant message.
2. Identify the issue type.
3. Draft a 2-3 sentence reply.
4. ALWAYS reply in the exact language the merchant used. If code-mixed Spanish-English,
   mirror code-mixed. If pure Spanish, reply in Spanish. If English, reply in US English.

[EXAMPLES]
Input: "Oye el settlement no llego ni despues de T+2"
Output: "Estamos revisando tu settlement, update en 2 horas."

Reminder: reply in the merchant's language. code-mixed in -> code-mixed out.

[FORMAT]
Reply with 2-3 sentences only. No JSON.
"""

# Self-checks against the success criteria:
ctx = FIXED.split("[CONTEXT]")[1].split("[INSTRUCTIONS]")[0]
assert "respond in the same language" not in ctx, "language rule must leave [CONTEXT]"
ins = FIXED.split("[INSTRUCTIONS]")[1].split("[EXAMPLES]")[0]
assert "ALWAYS reply in the exact language" in ins, "rule must be item 4 in [INSTRUCTIONS]"
between = FIXED.split("[EXAMPLES]")[1].split("[FORMAT]")[0]
assert "Reminder: reply in the merchant's language" in between, "end-anchor sits before [FORMAT]"
print(FIXED)
print("OK - rule relocated to [INSTRUCTIONS] item 4 + end-anchor before [FORMAT].")

#