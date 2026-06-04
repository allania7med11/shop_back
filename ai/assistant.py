import datetime
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from django.conf import settings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from ai.utils import get_products_index_path
from products.models import Product
from products.tasks import rebuild_product_index_task
from products.utils.orders import add_item_to_cart, get_draft_order

from .embed import format_product_info

# Set up the logger
logger = logging.getLogger(__name__)

# Verified live on the OpenAI models page (2026-06-01): the GPT-4 family is retired and
# gpt-5.4-mini is the current strongest mini — the right tier for a catalog tool-calling
# agent (fast/cheap tool calls). Change the model here only.
MODEL = "gpt-5.4-mini"


class CreatedByType(Enum):
    CLIENT = "client"
    ADMIN = "admin"
    CHATBOT = "chatbot"


@dataclass
class ChatHistoryMessage:
    content: str
    created_by: CreatedByType
    created_at: datetime


class ProductAssistant:
    # Safety cap on tool-calling rounds so a misbehaving model can't loop forever.
    max_tool_rounds: int = 5

    def __init__(self, user=None):
        # The chat owner (``chat.created_by``), used to scope the cart tools to THIS
        # user's draft order. None/anonymous -> cart tools are not bound.
        self.user = user
        # Two different models: embeddings turn text into vectors for catalog SEARCH
        # (similarity, no reasoning, cheap); the LLM is the agent that REASONS and REPLIES.
        # No model set -> the library default (text-embedding-ada-002). Index build
        # (ai/embed.py) must use the SAME model or similarity breaks.
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        # No temperature: gpt-5 models accept only their default, and langchain_openai
        # omits the parameter when it's unset, so leaving it off keeps the call valid.
        self.llm = ChatOpenAI(model=MODEL, openai_api_key=settings.OPENAI_API_KEY)
        self.vectorstore = self._load_vectorstore()

    def _load_vectorstore(self) -> FAISS:
        """
        Tries to load the vector store. If it fails, schedules a rebuild task.
        """
        try:
            return FAISS.load_local(
                get_products_index_path(), self.embeddings, allow_dangerous_deserialization=True
            )
        except Exception as e:
            logger.warning(f"Vector store failed to load: {e}. Scheduling rebuild.")
            rebuild_product_index_task.delay(reason="Auto-rebuild after load failure")
            return None

    def _format_product_info(self, docs: List[Document]) -> str:
        """Format products for the LLM, each tagged with ``[id: <slug>]`` for the cart tools.

        Tagged here, not in the embedded ``embed.format_product_info`` — keeps the slug out
        of the similarity vectors. add_to_cart validates the id, so a bad one fails loud.
        """
        product_info = []
        for doc in docs:
            product = Product.objects.get(slug=doc.metadata["product_slug"])
            content, _ = format_product_info(product)
            product_info.append(f"{content}\n[id: {product.slug}]")
        return "\n\n".join(product_info)

    def get_tools(self) -> list:
        """Tools bound to the agent.

        ``search_products`` is read-only (FAISS similarity + price filter) so it is safe
        for guests too. ``view_cart`` / ``add_to_cart`` operate on the chat owner's draft
        order and are bound ONLY for an authenticated user. Built as closures so they
        capture the already-loaded vector store / user instead of re-resolving on every
        call. With no usable index we bind no search → the model behaves like a plain call.
        """
        if not self.vectorstore:
            return []

        vectorstore = self.vectorstore

        @tool
        def search_products(query: str, max_price: Optional[float] = None) -> str:
            """Search the product catalog for items matching a description.

            Use this for ANY question about what products exist, their price, or their
            specs — you have no product knowledge of your own. ``max_price`` (optional)
            filters out anything priced above it (same currency as the catalog). Returns
            the matching products, or a note that none were found.
            """
            logger.info("tool search_products(query=%r, max_price=%r)", query, max_price)
            try:
                # Over-fetch on similarity, then apply price as a hard filter and
                # truncate. Price is a constraint, not a similarity signal, so it must be
                # applied AFTER ranking — a FAISS pre-filter would distort the ranking and
                # a small k could starve the answer (cheaper matches sitting just past k).
                docs = vectorstore.similarity_search(query, k=20)
            except Exception as e:
                logger.error("search_products similarity_search failed: %s", e)
                return "Product search is temporarily unavailable. Please try again."

            if max_price is not None:
                docs = [
                    d for d in docs
                    if d.metadata.get("current_price", float("inf")) <= max_price
                ]
            docs = docs[:5]

            if not docs:
                if max_price is not None:
                    return f"No matching products were found under {max_price}."
                return "No matching products were found."

            logger.info("search_products -> %d product(s)", len(docs))
            return self._format_product_info(docs)

        tools = [search_products]

        # The chat owner is always a real User row — a registered user OR a guest's lazy
        # User (get_actor). Either way the cart tools scope to THIS owner's draft order, so
        # guests get them too. The guard is just a None-safety check.
        if self.user:
            user = self.user

            @tool
            def view_cart() -> str:
                """Show what's currently in the customer's shopping cart.

                Use this whenever the customer asks what's in their cart. Returns each item
                with quantity and subtotal plus the total, or a note that the cart is empty.
                """
                logger.info("tool view_cart(user=%s)", getattr(user, "id", None))
                order = get_draft_order(user)
                items = list(order.items.select_related("product").all()) if order else []
                if not items:
                    return "The cart is empty."
                # Format money to 2 decimals — set_subtotal/total_amount return raw Decimals
                # with trailing zeros, which read awkwardly when the model echoes them back.
                lines = [
                    f"{i.quantity} x {i.product.name} — subtotal {i.set_subtotal():.2f}"
                    for i in items
                ]
                order.set_total_amount()
                lines.append(f"Total: {order.total_amount:.2f}")
                return "\n".join(lines)

            tools.append(view_cart)

            @tool
            def add_to_cart(product_id: str, quantity: int = 1) -> str:
                """Add a product to the customer's cart. Only call AFTER they confirm.

                ``product_id``: the ``[id: ...]`` from search_products results — never invent
                one. ``quantity`` (default 1) is ADDED to the current quantity. Returns the
                new quantity and cart total, or an error to act on.
                """
                logger.info(
                    "tool add_to_cart(user=%s, product_id=%r, quantity=%r)",
                    getattr(user, "id", None), product_id, quantity,
                )
                if quantity < 1:
                    return "Quantity must be at least 1."
                product = Product.objects.filter(slug=product_id).first()
                if not product:
                    return (
                        f"No product with id '{product_id}'. Call search_products first "
                        "to get a valid product id."
                    )
                try:
                    # mode="add" = increment. Shared atomic write lives in the orders service.
                    item = add_item_to_cart(user, product, quantity, mode="add")
                except Exception as e:
                    logger.error("add_to_cart failed for slug=%r: %s", product_id, e)
                    return "Couldn't add that to the cart right now. Please try again."

                order = item.order
                logger.info(
                    "add_to_cart -> item=%s qty=%s order_total=%s",
                    item.id, item.quantity, order.total_amount,
                )
                return (
                    f"Added {quantity} x {product.name}. Now {item.quantity} in the cart. "
                    f"Cart total: {order.total_amount:.2f}."
                )

            tools.append(add_to_cart)

        return tools

    def answer_question(self, chat_history: List[ChatHistoryMessage]) -> str:
        """
        Generate an answer to a customer question about products, running a bounded
        tool-calling loop. The model decides when to call ``search_products`` (no forced
        upfront retrieval), and the loop is capped at ``max_tool_rounds`` so it can't run
        forever. With no tools bound it behaves like a single LLM call.
        """
        if not chat_history:
            return "No question provided."

        chat_context = self.build_context(chat_history)
        lc_messages = self._build_prompt(chat_context, chat_history[-1].content)

        # Bind this assistant's tools (empty when there's no index -> single call).
        tools = self.get_tools()
        llm = self.llm.bind_tools(tools) if tools else self.llm
        tool_map = {t.name: t for t in tools}

        try:
            ai = None
            for round_num in range(1, self.max_tool_rounds + 1):
                ai = llm.invoke(lc_messages)
                lc_messages.append(ai)

                tool_calls = getattr(ai, "tool_calls", None)
                if not tool_calls:
                    return ai.content

                # Dedupe identical calls within a turn so a double-emitted write runs once.
                # Each tool_call_id still needs its own ToolMessage (API requirement).
                results_by_call = {}
                for call in tool_calls:
                    logger.info(
                        "round %d/%d: tool call %s args=%s",
                        round_num, self.max_tool_rounds, call["name"], call["args"],
                    )
                    key = (call["name"], json.dumps(call["args"], sort_keys=True))
                    if key in results_by_call:
                        result = results_by_call[key]
                    else:
                        tool = tool_map.get(call["name"])
                        result = (
                            tool.invoke(call["args"]) if tool else f"Unknown tool: {call['name']}"
                        )
                        results_by_call[key] = result
                    lc_messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

            # Exhausted the round cap.
            logger.warning("answer_question hit max_tool_rounds=%d", self.max_tool_rounds)
            return (ai.content if ai is not None else "") or (
                "I'm having trouble right now. Please try asking again."
            )
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm having trouble right now. Please try asking again."

    def _build_prompt(self, chat_context: str, current_question: str):
        """Build the message list fed to the model.

        Messages are constructed directly (not via a prompt template): chat history and
        product data can contain literal "{...}" which a template would try to resolve as
        variables and raise KeyError. These are final strings, not templates.
        """
        system = """You are a sharp, friendly sales associate for an online store.
Your job is to help the customer find the right product AND move them toward buying it.

You have NO product knowledge of your own. To answer anything about what products exist,
their price, or their specs, you MUST call the search_products tool first — never invent
or guess products, prices, or availability. If a search returns nothing, say so plainly
and offer the closest real option.

You can also manage the customer's cart: view_cart shows what's in it, and add_to_cart
puts an item in it. Two hard rules for add_to_cart:
- ALWAYS get the customer's explicit confirmation first ("Want me to add it?"). Never add
  something they haven't agreed to.
- Pass the product's [id: ...] from the search results as product_id — never make one up.

When you reply to the customer:
1. Lead with the benefit ("great for gaming / battery lasts all day"), then back it with
   one or two key specs from the search results.
2. Recommend ONE best-fit product — don't bury them in a list of options.
3. Be confident and concise: 2-3 short sentences.
4. READ THE CUSTOMER'S INTENT and match it. If they want "the best" / top camera / premium,
   double down on the strongest option and sell its strengths — do NOT offer a cheaper one.
   Only suggest a cheaper alternative if THEY signal price sensitivity ("too expensive",
   "on a budget", "anything cheaper").
5. Close with a nudge to act, and VARY it — never repeat the same closing line. Good closes:
   confirm the pick ("Want to go with this one?"), highlight what sets it apart, offer to add
   it to the cart, or ask one relevant follow-up (storage, color, use-case).
6. Persuade honestly: never pressure with false urgency or invented facts.

Examples:
- Budget-driven: "The Nord N200 is a smart pick under $200 — 90Hz screen and a 5000mAh
  battery that easily lasts all day. Want to go with this one?"
- Premium-driven ("I want the best camera"): "Then the iPhone 13 Pro Max is the one —
  12MP triple camera with 3x telephoto and ProMotion 120Hz, built for serious photography.
  It's our top shooter; want the 128GB or a larger size?\""""

        user_prompt = (
            f"Chat History:\n{chat_context}\n\n"
            f"Customer Question: {current_question}\n"
            "Please provide a helpful response."
        )

        return [SystemMessage(content=system), HumanMessage(content=user_prompt)]

    def build_context(self, chat_history: List[ChatHistoryMessage]) -> str:
        """
        Construct the context from chat history.

        Parameters:
        - chat_history: A list of ChatHistoryMessage instances.

        Returns:
        - A string representing the formatted chat history for context.
        """
        context_lines = []
        for msg in chat_history:
            if msg.created_by == CreatedByType.CLIENT:
                role = "Client"
            elif msg.created_by == CreatedByType.ADMIN:
                role = "Admin"
            elif msg.created_by == CreatedByType.CHATBOT:
                role = "Chatbot (previous AI response)"
            else:
                role = "Unknown"

            context_lines.append(f"{role} ({msg.created_at}): {msg.content}")

        return "\n".join(context_lines)
