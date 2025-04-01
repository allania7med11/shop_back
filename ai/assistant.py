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
            # Try to load existing index
            return FAISS.load_local("product_index", self.embeddings)
        except (FileNotFoundError, ValueError):
            # If no index exists, create new one
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
            content, _ = format_product_info(product)  # Use common function, ignore metadata
            product_info.append(content)
        return "\n".join(product_info)

    def answer_question(self, chat_history: List[ChatHistoryMessage]) -> str:
        """
        Generate an answer to a customer question about products.

        Parameters:
        - chat_history: A list of ChatHistoryMessage instances representing
                        the conversation history.
        """
        if not chat_history:
            return "No question provided."

        # Build the prompt with full chat context
        context_str = self.build_context(chat_history)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful shopping assistant for an e-commerce store.
            Your role is to help customers find products that match their needs.
            Use the provided product information to give accurate, helpful responses.
            If no products match the criteria, say so politely.
            Always mention specific products and their prices when relevant.""",
                ),
                (
                    "user",
                    f"""{context_str}
            Please provide a helpful response to the customer's question.""",
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
