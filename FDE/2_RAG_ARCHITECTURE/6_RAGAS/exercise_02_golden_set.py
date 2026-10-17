"""Exercise 2: create a 10-row golden set for a policy RAG.

Run with `python exercise_02_golden_set.py`; writes `golden.jsonl` to the
current working directory. Uses only the Python standard library.

Behavior: emits citation, paraphrase, multi-hop, French/German, and out-of-corpus
examples. Every JSONL record includes user_input, reference, reference_contexts,
and metadata.

Lesson: a useful evaluation set tests query variety and expected abstention, not
only easy questions. Regulatory references should be checked by a subject-matter
expert before they are used for production decisions.
"""

import json
from collections import Counter
from pathlib import Path


GOLDEN = [
    {
        "user_input": "Which GDPR article establishes the storage-limitation principle AcmeCorp implements in clause 4?",
        "reference": "GDPR Article 5(1)(e) establishes the storage-limitation principle; AcmeCorp Data-Protection Standard clause 4 implements it as a 90-day default retention window post-purpose unless a statute requires longer.",
        "reference_contexts": [
            "GDPR Art. 5(1)(e): personal data kept in a form permitting identification of data subjects for no longer than necessary.",
            "AcmeCorp Data-Protection Standard clause 4: default retention 90 days post-purpose.",
        ],
        "metadata": {"type": "citation", "lang": "en"},
    },
    {
        "user_input": "Under the EU AI Act, what obligation does Article 14 place on the high-risk AI system used in customer onboarding?",
        "reference": "EU AI Act Article 14 requires that high-risk AI systems be designed to enable effective human oversight, so the onboarding model must allow a competent person to intervene in or override its output.",
        "reference_contexts": [
            "EU AI Act Art. 14: high-risk AI systems shall be designed and developed to enable effective oversight by natural persons."
        ],
        "metadata": {"type": "citation", "lang": "en"},
    },
    {
        "user_input": "Which GDPR article supplies the legal basis the bank relies on for mandatory AML screening?",
        "reference": "GDPR Article 6(1)(c) supplies the legal basis: processing necessary for compliance with a legal obligation to which the controller is subject, which covers the bank's statutory anti-money-laundering screening duty.",
        "reference_contexts": [
            "GDPR Art. 6(1)(c): processing necessary for compliance with a legal obligation to which the controller is subject."
        ],
        "metadata": {"type": "citation", "lang": "en"},
    },
    {
        "user_input": "In plain terms, how long may AcmeCorp keep a customer's KYC file after the account is closed?",
        "reference": "AcmeCorp's internal AML/KYC procedure requires KYC records to be retained for five years after the business relationship ends, consistent with the applicable anti-money-laundering record-keeping obligation.",
        "reference_contexts": [
            "AcmeCorp AML/KYC Procedure Section 7: retain KYC records for 5 years after the end of the business relationship."
        ],
        "metadata": {"type": "paraphrase", "lang": "en"},
    },
    {
        "user_input": "Roughly speaking, what must the bank do before it acts on an automated AML alert?",
        "reference": "Before any adverse action is taken on an automated AML alert, a compliance analyst must review and confirm it, because the EU AI Act's human-oversight requirement precludes a solely automated adverse decision.",
        "reference_contexts": [
            "EU AI Act Art. 14: effective human oversight of high-risk AI systems.",
            "AcmeCorp AML/KYC Procedure Section 9: analyst confirmation required before filing a suspicious-activity report.",
        ],
        "metadata": {"type": "paraphrase", "lang": "en"},
    },
    {
        "user_input": "If a customer exercises the right to erasure, may AcmeCorp still retain their KYC records, and on what basis?",
        "reference": "Yes. GDPR Article 17(1) grants the right to erasure, but Article 17(3)(b) disapplies it where processing is necessary for compliance with a legal obligation, so AcmeCorp retains the KYC records for the five-year AML retention period notwithstanding the erasure request.",
        "reference_contexts": [
            "GDPR Art. 17(1): the data subject has the right to obtain erasure of personal data.",
            "GDPR Art. 17(3)(b): erasure does not apply where processing is necessary for compliance with a legal obligation.",
            "AcmeCorp AML/KYC Procedure Section 7: 5-year KYC retention.",
        ],
        "metadata": {"type": "multi_hop", "lang": "en"},
    },
    {
        "user_input": "When an AML model flags a customer, which two obligations - one from the GDPR, one from the EU AI Act - together govern how the bank must handle the flag?",
        "reference": "GDPR Article 22(1) restricts decisions based solely on automated processing that produce legal effects, and EU AI Act Article 14 mandates human oversight of high-risk AI; together they require a human analyst to review the flag before any adverse action.",
        "reference_contexts": [
            "GDPR Art. 22(1): right not to be subject to a decision based solely on automated processing producing legal effects.",
            "EU AI Act Art. 14: human oversight of high-risk AI systems.",
        ],
        "metadata": {"type": "multi_hop", "lang": "en"},
    },
    {
        "user_input": "Quelle est la duree de conservation par defaut des donnees personnelles selon la clause 4 de la norme de protection des donnees d'AcmeCorp?",
        "reference": "Selon la clause 4 de la norme de protection des donnees d'AcmeCorp, qui met en oeuvre l'article 5 du RGPD, la duree de conservation par defaut est de 90 jours apres la finalite, sauf obligation legale imposant une duree plus longue.",
        "reference_contexts": [
            "AcmeCorp Data-Protection Standard clause 4: conservation par defaut de 90 jours apres la finalite (met en oeuvre l'art. 5 du RGPD)."
        ],
        "metadata": {"type": "non_english", "lang": "fr"},
    },
    {
        "user_input": "Welcher Artikel der DSGVO regelt das Auskunftsrecht der betroffenen Person hinsichtlich ihrer bei AcmeCorp gespeicherten Daten?",
        "reference": "Artikel 15 der DSGVO regelt das Auskunftsrecht der betroffenen Person; AcmeCorp muss auf Anfrage bestaetigen, welche personenbezogenen Daten verarbeitet werden, und eine Kopie dieser Daten bereitstellen.",
        "reference_contexts": [
            "DSGVO Art. 15: Auskunftsrecht der betroffenen Person ueber die Verarbeitung ihrer personenbezogenen Daten."
        ],
        "metadata": {"type": "non_english", "lang": "de"},
    },
    {
        "user_input": "What does AcmeCorp's life-insurance underwriting policy say about processing genetic data?",
        "reference": "The supplied AcmeCorp policy corpus contains no life-insurance underwriting or genetic-data policy; the system should state that it cannot answer from the available sources.",
        "reference_contexts": [],
        "metadata": {"type": "out_of_corpus", "lang": "en"},
    },
]


def main():
    output = Path.cwd() / "golden.jsonl"
    with output.open("w", encoding="utf-8") as file:
        for row in GOLDEN:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    types = Counter(row["metadata"]["type"] for row in GOLDEN)
    non_english = [
        row["metadata"]["lang"]
        for row in GOLDEN
        if row["metadata"]["lang"] != "en"
    ]
    assert len(GOLDEN) == 10
    assert non_english
    print(f"{output}: {len(GOLDEN)} rows")
    print("query types:", dict(types))
    print("non-English languages:", sorted(set(non_english)))


if __name__ == "__main__":
    main()
