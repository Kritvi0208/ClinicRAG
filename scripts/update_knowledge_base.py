import sys
from pathlib import Path
from langchain_core.documents import Document

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.logger import logger
from src.loaders import MedicalDocumentLoader
from src.splitter import MedicalTextSplitter
from src.parser import MedicalDocumentParser
from src.vector_store import MedicalVectorStore

def main():
    logger.info("Starting update_knowledge_base script...")
    store = MedicalVectorStore()
    
    # Verify DB connection and existing document count
    try:
        db = store.get_db()
        doc_count = store.get_document_count()
        logger.info(f"Database contains {doc_count} chunks.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

    # If database is completely empty, suggest running build_vector_store.py
    if doc_count == 0:
        print("Vector database is empty. Please run build_vector_store.py first.")
        sys.exit(0)

    # Extract all currently indexed file sources from metadata
    indexed_sources = set()
    try:
        collection = db._collection
        # Get all metadatas
        results = collection.get(include=["metadatas"])
        if results and "metadatas" in results:
            for meta in results["metadatas"]:
                if meta and "source" in meta:
                    # Convert to string and absolute path format
                    indexed_sources.add(str(Path(meta["source"]).resolve()))
        logger.info(f"Retrieved {len(indexed_sources)} unique indexed source files.")
    except Exception as e:
        print(f"Error querying existing sources: {e}")
        logger.error(f"Error querying existing sources: {e}")
        sys.exit(1)

    # Discover all documents in knowledge base directory
    loader = MedicalDocumentLoader(config.KNOWLEDGE_BASE_DIR)
    all_files = list(loader._get_files())
    
    new_files = []
    for file_path in all_files:
        abs_path_str = str(file_path.resolve())
        if abs_path_str not in indexed_sources:
            new_files.append(file_path)

    if not new_files:
        print("All documents are already indexed. Database is up-to-date!")
        logger.info("No new files found. Database is up-to-date.")
        return

    print(f"Found {len(new_files)} new files to index:")
    for f in new_files:
        print(f" - {f.name}")

    # Load and process only the new files
    loaded_docs = []
    for file_path in new_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            relative_path = file_path.relative_to(config.KNOWLEDGE_BASE_DIR)
            category = relative_path.parts[0] if len(relative_path.parts) > 1 else "General"
            
            section = "Introduction"
            for line in content.splitlines():
                if line.startswith("# ") or line.startswith("## "):
                    section = line.replace("#", "").strip()
                    break
                    
            metadata = {
                "source": str(file_path.resolve()),
                "source_name": file_path.name,
                "category": category,
                "section": section,
                "file_size": file_path.stat().st_size
            }
            loaded_docs.append(Document(page_content=content, metadata=metadata))
        except Exception as e:
            logger.error(f"Failed to load new file {file_path}: {e}")

    if not loaded_docs:
        print("No documents were successfully loaded.")
        return

    print(f"Splitting new documents...")
    splitter = MedicalTextSplitter()
    chunks = splitter.split_documents(loaded_docs)

    print("Parsing and cleaning chunks...")
    doc_parser = MedicalDocumentParser()
    processed_chunks = doc_parser.parse_sections(chunks)

    print(f"Adding {len(processed_chunks)} new chunks to ChromaDB...")
    success = store.add_documents(processed_chunks)

    if success:
        new_total = store.get_document_count()
        print("\n=== Update Statistics ===")
        print(f"Successfully added new documents!")
        print(f"New documents added: {len(new_files)}")
        print(f"Total chunks in database: {new_total}")
        print("=========================")
        logger.info(f"Database updated. Added {len(new_files)} files. Total chunks: {new_total}")
    else:
        print("Failed to add new documents to vector store.")

if __name__ == "__main__":
    main()
