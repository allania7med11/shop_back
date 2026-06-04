"""Behavioral evals for ProductAssistant — runs the REAL model (costs tokens), so it's
kept separate from the mock-LLM unit tests in ai/tests.py.

Run:
    docker compose exec shop_back python manage.py shell -c "from ai.evals import run; run()"
"""
import datetime

from django.contrib.auth.models import User

from ai.assistant import ChatHistoryMessage, CreatedByType, ProductAssistant


def _history(text):
    """Wrap one customer message as the chat history the agent expects."""
    return [
        ChatHistoryMessage(
            content=text,
            created_by=CreatedByType.CLIENT,
            created_at=datetime.datetime(2026, 6, 1),
        )
    ]


# Each case: an input + the customer's screen + a check on what the agent did.
# The check reads only the agent's existing outputs (reply.navigate, reply.content).
CASES = [
    {
        "name": "no_nav_offer_when_on_cart",
        "input": "can you show me my cart?",
        "client_context": {"current_path": "/cart/"},
        "check": lambda reply: reply.navigate != "/cart/",
        "why": "customer is already on /cart/ — the agent must not navigate them there",
    },
    {
        "name": "confirm_before_write",
        "input": "i'm looking for a cheap phone under 200",
        # A write tool dirties the "Cart" cache tag; browsing must not trigger one.
        "check": lambda reply: "Cart" not in reply.invalidates,
        "why": "customer is browsing, not confirmed — the agent must not write to the cart",
    },
    {
        # Positive pair to confirm_before_write: together they pin "writes ONLY after confirm".
        "name": "writes_when_confirmed",
        "input": "yes, add the OnePlus Nord N200 to my cart",
        "check": lambda reply: "Cart" in reply.invalidates,
        "why": "the customer confirmed — the agent MUST write to the cart",
    },
    {
        # Positive pair to no_nav_offer_when_on_cart: it MUST navigate when actually asked.
        "name": "navigates_when_asked",
        "input": "take me to my cart",
        "client_context": {"current_path": "/"},
        "check": lambda reply: reply.navigate == "/cart/",
        "why": "asked from the home page — the agent must navigate to /cart/",
    },
    {
        "name": "comparison_uses_bullets",
        "input": "compare the macbook pro and the surface laptop 4 for coding",
        "check": lambda reply: any(
            line.lstrip().startswith("- ") for line in reply.content.splitlines()
        ),
        "why": "a comparison should be a bullet list, not a prose wall",
    },
    {
        "name": "bold_capped_one_per_line",
        "input": "what's the best laptop for a senior engineer?",
        # "**" comes in pairs, so >2 on a line means more than one bold span.
        "check": lambda reply: all(
            line.count("**") <= 2 for line in reply.content.splitlines()
        ),
        "why": "at most one **bold** span per line — no spec-bolding noise",
    },
]


def run():
    user = User.objects.filter(is_superuser=False).first()
    assistant = ProductAssistant(user=user)

    passed = 0
    for case in CASES:
        reply = assistant.answer_question(
            _history(case["input"]), client_context=case.get("client_context")
        )
        ok = case["check"](reply)
        passed += int(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {case['name']}  (navigate={reply.navigate!r})")
        if not ok:
            print(f"    expected: {case['why']}")
            print(f"    reply:    {reply.content[:140]}")

    print(f"\n{passed}/{len(CASES)} passed")
