from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.config import config
from src.logger import logger

class MedicalTextSplitter:
    """Wraps RecursiveCharacterTextSplitter to split medical documents while preserving section metadata."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        # Priority separators: Paragraphs, Sentences, Words
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits a list of documents into chunked documents."""
        if not documents:
            logger.warning("Empty documents list passed to text splitter.")
            return []
            
        logger.info(f"Splitting {len(documents)} documents (size={self.chunk_size}, overlap={self.chunk_overlap}).")
        chunks = self.splitter.split_documents(documents)
        
        # Post-process chunks to inject unique chunk IDs
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source_name', 'doc')}_chunk_{idx}"
            
        logger.info(f"Created {len(chunks)} text chunks.")
        return chunks
