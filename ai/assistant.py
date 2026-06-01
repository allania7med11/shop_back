import datetime
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List

from django.conf import settings
from langchain.schema import Document
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from ai.utils import get_products_index_path
from products.models import Product
from products.tasks import rebuild_product_index_task

from .embed import format_product_info

# Set up the logger
logger = logging.getLogger(__name__)


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

    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview", temperature=0.7, openai_api_key=settings.OPENAI_API_KEY
        )
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

    def _get_relevant_products(self, chat_context: str, k: int = 5) -> List[Document]:
        """
        Retrieve relevant product documents based on the chat context.
        This helps identify products mentioned in the conversation.
        """
        if not self.vectorstore:
            logger.warning("Vectorstore is not loaded. Skipping similarity search.")
            return []

        try:
            results = self.vectorstore.similarity_search(chat_context, k=k)
            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return []

    def _format_product_info(self, docs: List[Document]) -> str:
        """Format product information for the LLM context."""
        product_info = []
        for doc in docs:
            product = Product.objects.get(slug=doc.metadata["product_slug"])
            content, _ = format_product_info(product)
            product_info.append(content)
        return "\n".join(product_info)

    def get_tools(self) -> list:
        """Tools bound to the agent. Empty for now (Commit 1: loop scaffold only)
        so the assistant behaves like today's single call. search_products /
        view_cart / add_to_cart land in later commits."""
        return []

    def answer_question(self, chat_history: List[ChatHistoryMessage]) -> str:
        """
        Generate an answer to a customer question about products, running a
        bounded tool-calling loop. With no tools bound (current state) this
        behaves like a single LLM call.
        """
        if not chat_history:
            return "No question provided."

        # Build the chat context once and reuse it
        chat_context = self.build_context(chat_history)

        # Get relevant products based on the chat context
        relevant_products = self._get_relevant_products(chat_context)
        if not relevant_products:
            return (
                "I apologize, but I couldn't find any products matching your question. "
                "Could you please rephrase or ask about something else?"
            )

        # Format product information
        product_info = self._format_product_info(relevant_products)

        lc_messages = self._build_prompt(chat_context, product_info, chat_history[-1].content)

        # Bind this assistant's tools (empty for now -> behaves like a single call).
        tools = self.get_tools()
        llm = self.llm.bind_tools(tools) if tools else self.llm
        tool_map = {t.name: t for t in tools}

        try:
            ai = None
            for _ in range(self.max_tool_rounds):
                ai = llm.invoke(lc_messages)
                lc_messages.append(ai)

                tool_calls = getattr(ai, "tool_calls", None)
                if not tool_calls:
                    return ai.content

                # Run each requested tool and feed the result back to the model.
                for call in tool_calls:
                    tool = tool_map.get(call["name"])
                    result = tool.invoke(call["args"]) if tool else f"Unknown tool: {call['name']}"
                    lc_messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

            # Exhausted the round cap.
            return (ai.content if ai is not None else "") or (
                "I'm having trouble right now. Please try asking again."
            )
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm having trouble right now. Please try asking again."

    def _build_prompt(self, chat_context: str, product_info: str, current_question: str):
        """Build the message list fed to the model.

        Messages are constructed directly (not via a prompt template): chat
        history and product data can contain literal "{...}" which a template
        would try to resolve as variables and raise KeyError. These are final
        strings, not templates.
        """
        system = """You are a helpful shopping assistant. Follow these rules:
1. Use 1-2 short sentences only
2. Only state key product specs from the description
3. Use simple, clear language
4. End with a brief question
5. Stay under 30 words total

Example format:
[Key product specs] Would you like to know about [feature]?"""

        user_prompt = (
            f"Chat History:\n{chat_context}\n\n"
            f"Product Information:\n{product_info}\n\n"
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
