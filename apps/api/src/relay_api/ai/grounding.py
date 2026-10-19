"""A deliberately extractive contract for financial and service facts.

Fact IDs alone do not validate prose. The model may arrange verified statements
and choose an introduction, but cannot invent or reassign their values.
"""

INTRODUCTIONS = (
    "Here's what I could verify:",
    "I checked the information available for your account.",
)


def statements(facts: list[str]) -> list[str]:
    prefixes = {
        "Account service: ": "",
        "Billing service: ": "Your bill: ",
        "Billing item: ": "",
        "Network service reports ": "Network status: ",
        "Legacy XML: ": "Subscriber record: ",
    }
    result = []
    for fact in facts:
        for prefix, replacement in prefixes.items():
            if fact.startswith(prefix):
                fact = replacement + fact[len(prefix) :]
                break
        result.append(fact[:1].upper() + fact[1:])
    return result


def validate_statements(answer: str, facts: list[str]) -> None:
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]
    if paragraphs and paragraphs[0] in INTRODUCTIONS:
        paragraphs.pop(0)
    expected = statements(facts)
    if sorted(paragraphs) != sorted(expected):
        raise ValueError("unsupported_semantic_claim")
