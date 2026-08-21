from typing import Any, Dict, List, Optional
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import config
from src.retriever import MedicalRetriever
from src.prompts import get_rag_prompt_template
from src.logger import logger

class MedicalRAGChain:
    """Implements LCEL (LangChain Expression Language) for context-enriched queries."""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, retriever: MedicalRetriever):
        self.llm = llm
        self.retriever = retriever
        self.prompt = get_rag_prompt_template()
        self._build_chain()

    def _format_docs(self, docs: List[Document]) -> str:
        """Formats Document content for injection into the prompt template."""
        if not docs:
            return "No verified medical documents found in database."
        
        formatted_chunks = []
        for idx, doc in enumerate(docs):
            formatted_chunks.append(
                f"--- Document {idx+1} ---\n"
                f"Source: {doc.metadata.get('source_name', 'Unknown')}\n"
                f"Category: {doc.metadata.get('category', 'General')}\n"
                f"Section: {doc.metadata.get('section', 'General')}\n"
                f"Content: {doc.page_content}\n"
            )
        return "\n".join(formatted_chunks)

    def _build_chain(self):
        """Assembles the LCEL runnable chain."""
        # Custom retriever step within LCEL pipeline
        def retrieve_and_format(inputs: Dict[str, Any]) -> str:
            query = inputs["input"]
            docs = self.retriever.retrieve(query)
            # Save the retrieved docs in a thread-safe way to access later for source attribution
            inputs["retrieved_docs"] = docs
            return self._format_docs(docs)

        # LCEL chain building
        self.chain = (
            RunnablePassthrough.assign(context=retrieve_and_format)
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def run(self, user_input: str, chat_history: List[Any]) -> Dict[str, Any]:
        """Runs the RAG chain and returns both the answer text and source document metadata."""
        logger.info(f"Running RAG Chain for query: '{user_input[:50]}...'")
        
        # Prepare inputs. We use a container dictionary.
        inputs = {
            "input": user_input,
            "chat_history": chat_history,
            "retrieved_docs": []  # This list will be populated inside retrieve_and_format
        }
        
        try:
            # Execute LCEL chain
            output = self.chain.invoke(inputs)
            
            return {
                "output": output,
                "sources": inputs.get("retrieved_docs", [])
            }
        except Exception as e:
            logger.error(f"RAG Chain invocation failure: {e}")
            return {
                "output": f"Failed to retrieve context and generate response: {str(e)}",
                "sources": []
            }
        
# For direct RAG execution if required outside the Agent
def build_rag_chain(llm: ChatGoogleGenerativeAI, retriever: MedicalRetriever) -> MedicalRAGChain:
    return MedicalRAGChain(llm, retriever)
