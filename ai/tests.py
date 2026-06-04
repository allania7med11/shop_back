"""Eval / unit tests for the agentic ProductAssistant (SHP-8).

Deterministic — they need no OpenAI key, no FAISS index, and no database:
- the LLM is a scripted fake (``FakeLLM``) that emits tool calls / final answers,
- the vector store is a stub returning fixed ``Document`` objects,
- ``_format_product_info`` is stubbed so no ``Product`` rows are required.

They cover the three things the SHP-8 plan calls out for the search tool: the tool
actually fires, the ``max_price`` ceiling holds (over-fetch -> filter -> truncate), and
the bounded loop returns a final answer in a small number of rounds. The live
"warm jacket under $50" flow (real model + index) stays a manual verification step.
"""
import datetime

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from ai.assistant import ChatHistoryMessage, CreatedByType, ProductAssistant


class FakeLLM:
    """Scripted stand-in for ChatOpenAI: returns queued messages and records how many
    times it was invoked and which tools were bound to it."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.invocations = 0
        self.bound_tools = None

    def bind_tools(self, tools):
        self.bound_tools = tools
        return self

    def invoke(self, messages):
        self.invocations += 1
        return self._responses.pop(0)


class FakeVectorStore:
    """Returns a fixed document set and records the ``k`` it was asked for."""

    def __init__(self, docs):
        self._docs = docs
        self.last_k = None

    def similarity_search(self, query, k=5):
        self.last_k = k
        return list(self._docs)


def _doc(slug, price):
    return Document(page_content=slug, metadata={"product_slug": slug, "current_price": price})


def _assistant(llm, docs):
    """Build a ProductAssistant without running __init__ (so no key/index/DB)."""
    a = ProductAssistant.__new__(ProductAssistant)
    a.max_tool_rounds = 5
    a.user = None  # no chat owner -> only the read-only search tool is bound
    a.llm = llm
    a.vectorstore = FakeVectorStore(docs)
    # Stub the DB-backed formatter: format straight from the doc page_content.
    a._format_product_info = lambda docs: "\n".join(d.page_content for d in docs)
    return a


def _tool_call(query, max_price=None):
    args = {"query": query}
    if max_price is not None:
        args["max_price"] = max_price
    return AIMessage(content="", tool_calls=[{"name": "search_products", "args": args, "id": "c1"}])


def _history(text):
    return [
        ChatHistoryMessage(
            content=text,
            created_by=CreatedByType.CLIENT,
            created_at=datetime.datetime(2026, 6, 1),
        )
    ]


def test_search_products_filters_by_max_price():
    docs = [_doc("cheap-tee", 20.0), _doc("mid-jacket", 45.0), _doc("lux-coat", 120.0)]
    tool = _assistant(FakeLLM([]), docs).get_tools()[0]

    out = tool.invoke({"query": "jacket", "max_price": 50.0})

    assert "cheap-tee" in out and "mid-jacket" in out
    assert "lux-coat" not in out  # price ceiling holds


def test_search_products_overfetches_then_truncates_to_five():
    a = _assistant(FakeLLM([]), [_doc(f"p{i}", 10.0) for i in range(12)])
    tool = a.get_tools()[0]

    out = tool.invoke({"query": "anything"})

    assert a.vectorstore.last_k == 20  # over-fetch on similarity, not k=5
    assert len([line for line in out.splitlines() if line]) == 5  # truncated to top 5


def test_search_products_reports_none_found_instead_of_empty():
    tool = _assistant(FakeLLM([]), [_doc("lux-coat", 120.0)]).get_tools()[0]

    out = tool.invoke({"query": "jacket", "max_price": 50.0})

    assert "No matching products" in out  # explicit message, never an empty string


def test_loop_runs_one_tool_round_then_final_answer():
    final = AIMessage(content="The warm jacket is $40. Want details?")
    llm = FakeLLM([_tool_call("warm jacket", 50.0), final])
    a = _assistant(llm, [_doc("warm-jacket", 40.0)])

    reply = a.answer_question(_history("find a warm jacket under $50"))

    assert reply == final.content
    assert llm.invocations == 2  # exactly one tool round, then the final answer
    assert llm.bound_tools and llm.bound_tools[0].name == "search_products"


def test_no_tool_call_returns_immediately():
    llm = FakeLLM([AIMessage(content="Hi! What are you shopping for today?")])
    a = _assistant(llm, [_doc("x", 1.0)])

    reply = a.answer_question(_history("hi"))

    assert reply == "Hi! What are you shopping for today?"
    assert llm.invocations == 1  # no tool round when the model doesn't call a tool


def test_loop_is_bounded_when_model_always_calls_tools():
    # A model that calls the tool every round must still stop at max_tool_rounds.
    llm = FakeLLM([_tool_call("jacket") for _ in range(10)])
    a = _assistant(llm, [_doc("warm-jacket", 40.0)])
    a.max_tool_rounds = 3

    a.answer_question(_history("loop forever please"))

    assert llm.invocations == 3  # capped, never runs all 10
