"""Exercise 1: compare fixed-size and sentence-boundary chunking.

Run with Python 3; no API key or external package is needed. This uses synthetic teaching
text, not authoritative GDPR language.

Embedding note: the notebook's live path used OpenAI text-embedding-3-small, but this
exercise does not need embeddings. Sentence boundaries can preserve a long numbered
sub-clause that a fixed character window splits.
"""

import re


ARTICLE_7 = """GDPR Article 7 - Conditions for consent (synthetic teaching text)

7(1) Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented to processing of personal data.

7(2) If consent is given in a written declaration which also concerns other matters, the request for consent shall be presented in a manner clearly distinguishable from the other matters, in an intelligible and easily accessible form, using clear and plain language.

7(3) The data subject shall have the right to withdraw consent at any time. The withdrawal shall not affect the lawfulness of processing based on consent before withdrawal.

7(4) When assessing whether consent is freely given, account shall be taken of whether performance of a contract is conditional on consent to processing not necessary for that contract.

7(5) Consent shall be as easy to withdraw as to give. The controller shall not degrade the service where a data subject withdraws consent for non-essential processing.

7(6) Consent obtained through fraud, coercion, or a pre-ticked box shall be void from inception and shall not constitute a lawful basis for processing.

7(7) Consent withdrawal mechanisms shall meet the following requirements:
(a) shall be as easy to use as the mechanism to give consent, including in language and accessibility;
(b) shall be available in every language in which consent was originally requested, including but not limited to Spanish, Mandarin, French, Arabic, Japanese, German, Portuguese, Hindi, Bengali, Russian, and any other notified language that the controller relied upon at the point of collection, together with an accessible alternative for data subjects who depend on assistive technology, so that no data subject is ever compelled to operate in a language or a modality they do not use in order to exercise the right to withdraw a previously given consent;
(c) shall not require disclosure of additional personal data beyond what is necessary to authenticate the data subject.

7(8) The controller shall maintain a record of consent and withdrawal and make that record available to the supervisory authority on request.
"""


def fixed_chunks(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start : start + size]
        if chunk.strip():
            chunks.append(chunk)
        start += size - overlap
    return chunks


def sentence_chunks(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.;])\s+(?=[A-Z0-9(])", text) if part.strip()]


def main() -> None:
    fixed = fixed_chunks(ARTICLE_7)
    sentence = sentence_chunks(ARTICLE_7)
    print("\n=== Fixed-size chunks ===")
    for index, chunk in enumerate(fixed, 1):
        print(f"\n[fixed {index}/{len(fixed)}]\n{chunk}")
    print("\n=== Sentence-boundary chunks ===")
    for index, chunk in enumerate(sentence, 1):
        print(f"\n[sentence {index}/{len(sentence)}]\n{chunk}")

    clause_start = "(b) shall be available in every language"
    clause_end = "withdraw a previously given consent"
    intact = next(chunk for chunk in sentence if clause_start in chunk)
    fixed_head = [index for index, chunk in enumerate(fixed) if clause_start in chunk]
    fixed_tail = [index for index, chunk in enumerate(fixed) if clause_end in chunk]
    fixed_whole = [index for index, chunk in enumerate(fixed) if intact in chunk]
    sentence_whole = [chunk for chunk in sentence if clause_start in chunk and clause_end in chunk]

    print(f"Fixed-size chunks: {len(fixed)}; sentence chunks: {len(sentence)}")
    print(f"Sub-clause (b) length: {len(intact)} characters")
    print("Fixed chunk indices containing beginning:", fixed_head)
    print("Fixed chunk indices containing ending:", fixed_tail)
    print("Fixed chunk indices containing whole clause:", fixed_whole)
    print("Sentence chunks containing whole clause:", len(sentence_whole))
    print("Lesson: size limits can sever semantic units; boundary-aware chunking may preserve them.")


if __name__ == "__main__":
    main()

"""
=== Fixed-size chunks ===

[fixed 1/5]
GDPR Article 7 - Conditions for consent (synthetic teaching text)

7(1) Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented to processing of personal data.

7(2) If consent is given in a written declaration which also concerns other matters, the request for consent shall be presented in a manner clearly distinguishable from the other matters, in an intelligible and easily accessible form, using clear and plain language.

7(3) The

[fixed 2/5]
e form, using clear and plain language.

7(3) The data subject shall have the right to withdraw consent at any time. The withdrawal shall not affect the lawfulness of processing based on consent before withdrawal.

7(4) When assessing whether consent is freely given, account shall be taken of whether performance of a contract is conditional on consent to processing not necessary for that contract.

7(5) Consent shall be as easy to withdraw as to give. The controller shall not degrade the service

[fixed 3/5]
give. The controller shall not degrade the service where a data subject withdraws consent for non-essential processing.

7(6) Consent obtained through fraud, coercion, or a pre-ticked box shall be void from inception and shall not constitute a lawful basis for processing.

7(7) Consent withdrawal mechanisms shall meet the following requirements:
(a) shall be as easy to use as the mechanism to give consent, including in language and accessibility;
(b) shall be available in every language in which

[fixed 4/5]

(b) shall be available in every language in which consent was originally requested, including but not limited to Spanish, Mandarin, French, Arabic, Japanese, German, Portuguese, Hindi, Bengali, Russian, and any other notified language that the controller relied upon at the point of collection, together with an accessible alternative for data subjects who depend on assistive technology, so that no data subject is ever compelled to operate in a language or a modality they do not use in order to e

[fixed 5/5]
nguage or a modality they do not use in order to exercise the right to withdraw a previously given consent;
(c) shall not require disclosure of additional personal data beyond what is necessary to authenticate the data subject.

7(8) The controller shall maintain a record of consent and withdrawal and make that record available to the supervisory authority on request.


=== Sentence-boundary chunks ===

[sentence 1/12]
GDPR Article 7 - Conditions for consent (synthetic teaching text)

7(1) Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented to processing of personal data.

[sentence 2/12]
7(2) If consent is given in a written declaration which also concerns other matters, the request for consent shall be presented in a manner clearly distinguishable from the other matters, in an intelligible and easily accessible form, using clear and plain language.

[sentence 3/12]
7(3) The data subject shall have the right to withdraw consent at any time.

[sentence 4/12]
The withdrawal shall not affect the lawfulness of processing based on consent before withdrawal.

[sentence 5/12]
7(4) When assessing whether consent is freely given, account shall be taken of whether performance of a contract is conditional on consent to processing not necessary for that contract.

[sentence 6/12]
7(5) Consent shall be as easy to withdraw as to give.

[sentence 7/12]
The controller shall not degrade the service where a data subject withdraws consent for non-essential processing.

[sentence 8/12]
7(6) Consent obtained through fraud, coercion, or a pre-ticked box shall be void from inception and shall not constitute a lawful basis for processing.

[sentence 9/12]
7(7) Consent withdrawal mechanisms shall meet the following requirements:
(a) shall be as easy to use as the mechanism to give consent, including in language and accessibility;

[sentence 10/12]
(b) shall be available in every language in which consent was originally requested, including but not limited to Spanish, Mandarin, French, Arabic, Japanese, German, Portuguese, Hindi, Bengali, Russian, and any other notified language that the controller relied upon at the point of collection, together with an accessible alternative for data subjects who depend on assistive technology, so that no data subject is ever compelled to operate in a language or a modality they do not use in order to exercise the right to withdraw a previously given consent;

[sentence 11/12]
(c) shall not require disclosure of additional personal data beyond what is necessary to authenticate the data subject.

[sentence 12/12]
7(8) The controller shall maintain a record of consent and withdrawal and make that record available to the supervisory authority on request.
Fixed-size chunks: 5; sentence chunks: 12
Sub-clause (b) length: 556 characters
Fixed chunk indices containing beginning: [2, 3]
Fixed chunk indices containing ending: [4]
Fixed chunk indices containing whole clause: []
Sentence chunks containing whole clause: 1
Lesson: size limits can sever semantic units; boundary-aware chunking may preserve them.
"""