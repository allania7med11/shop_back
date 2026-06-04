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
