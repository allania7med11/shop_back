import datetime
from dataclasses import dataclass
from enum import Enum
from typing import List

from django.conf import settings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from products.models import Product

from .embed import build_product_documents, format_product_info


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
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview", temperature=0.7, openai_api_key=settings.OPENAI_API_KEY
        )
        self.vectorstore = self._initialize_vectorstore()

    def _initialize_vectorstore(self) -> FAISS:
        """Initialize or load the vector store with product data."""
        try:
            return FAISS.load_local("product_index", self.embeddings)
        except (FileNotFoundError, ValueError):
            documents = build_product_documents()
            return FAISS.from_documents(documents, self.embeddings)

    def _get_relevant_products(self, query: str, k: int = 5) -> List[Document]:
        """Retrieve relevant product documents based on the query."""
        return self.vectorstore.similarity_search(query, k=k)

    def _format_product_info(self, docs: List[Document]) -> str:
        """Format product information for the LLM context."""
        product_info = []
        for doc in docs:
            product = Product.objects.get(slug=doc.metadata["product_slug"])
            content, _ = format_product_info(product)
            product_info.append(content)
        return "\n".join(product_info)

    def answer_question(self, chat_history: List[ChatHistoryMessage]) -> str:
        """
        Generate an answer to a customer question about products.
        """
        if not chat_history:
            return "No question provided."

        # Get the last user message
        last_message = next(
            msg for msg in reversed(chat_history) if msg.created_by == CreatedByType.CLIENT
        )

        # Get relevant products based on the question
        relevant_products = self._get_relevant_products(last_message.content)
        if not relevant_products:
            return (
                "I apologize, but I couldn't find any products matching your question. "
                "Could you please rephrase or ask about something else?"
            )

        # Format product information and chat context
        product_info = self._format_product_info(relevant_products)
        chat_context = self.build_context(chat_history)

        # Build the prompt with product info, chat context, and web info
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful shopping assistant. Follow these rules:
                1. Use 1-2 short sentences only
                2. Only state key product specs from the description
                3. Use simple, clear language
                4. End with a brief question
                5. Stay under 30 words total

                Example format:
                [Key product specs] Would you like to know about [feature]?""",
                ),
                (
                    "user",
                    f"""Chat History:
                {chat_context}
                Product Information:
                {product_info}
                Customer Question: {last_message.content}
                Please provide a helpful response.""",
                ),
            ]
        )

        # Generate the response
        chain = prompt | self.llm
        response = chain.invoke({})

        return response.content

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
