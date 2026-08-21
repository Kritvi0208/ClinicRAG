from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from src.config import config
from src.embeddings import get_embeddings_model
from src.logger import logger

class MedicalVectorStore:
    """Interface to manage the persistent ChromaDB lifecycle."""
    
    def __init__(self):
        self.persist_dir = str(config.CHROMA_DB_DIR)
        self._db: Optional[Chroma] = None

    def get_db(self) -> Chroma:
        """Lazy-loads and caches the persistent ChromaDB instance."""
        if self._db is not None:
            return self._db
            
        try:
            embeddings = get_embeddings_model()
            logger.info(f"Connecting to persistent ChromaDB at {self.persist_dir}")
            self._db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=embeddings
            )
            return self._db
        except Exception as e:
            logger.error(f"Failed to load persistent ChromaDB: {e}")
            raise

    def add_documents(self, documents: List[Document]) -> bool:
        """Adds a list of chunks/documents to ChromaDB."""
        if not documents:
            logger.warning("No documents to add to vector store.")
            return False
            
        try:
            db = self.get_db()
            logger.info(f"Indexing {len(documents)} document chunks into ChromaDB...")
            db.add_documents(documents)
            logger.info("Successfully added documents to ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")
            return False

    def clean_database(self) -> bool:
        """Wipes the database directory and resets the database instance."""
        try:
            self._db = None
            db_path = Path(self.persist_dir)
            if db_path.exists():
                import shutil
                shutil.rmtree(db_path)
                logger.info(f"Wiped ChromaDB directory at {self.persist_dir}")
            db_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error cleaning ChromaDB: {e}")
            return False

    def get_document_count(self) -> int:
        """Returns the number of documents currently stored in ChromaDB."""
        try:
            db = self.get_db()
            # Chroma internal API to get total items
            return db._collection.count()
        except Exception as e:
            logger.error(f"Error getting ChromaDB document count: {e}")
            return 0
