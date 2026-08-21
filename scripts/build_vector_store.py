import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.logger import logger
from src.loaders import MedicalDocumentLoader
from src.splitter import MedicalTextSplitter
from src.parser import MedicalDocumentParser
from src.vector_store import MedicalVectorStore

def main():
    parser = argparse.ArgumentParser(description="Seed and build the ClinicRAG Vector Store.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild of the vector database by wiping existing entries first."
    )
    args = parser.parse_args()

    logger.info("Starting build_vector_store script...")
    store = MedicalVectorStore()

    # Check if DB directory is not empty
    db_exists = False
    db_path = Path(store.persist_dir)
    if db_path.exists() and any(db_path.iterdir()):
        db_exists = True

    if db_exists and not args.rebuild:
        # Check current count
        doc_count = store.get_document_count()
        if doc_count > 0:
            print(f"ChromaDB already exists at {store.persist_dir} with {doc_count} document chunks.")
            print("Skipping rebuild. Use the --rebuild flag to wipe and rebuild.")
            logger.info("ChromaDB already exists. Skipping rebuild.")
            return

    if args.rebuild:
        print("Wiping existing database as requested by --rebuild...")
        store.clean_database()

    print(f"Loading files from knowledge base: {config.KNOWLEDGE_BASE_DIR}")
    loader = MedicalDocumentLoader(config.KNOWLEDGE_BASE_DIR)
    raw_docs = loader.load()

    if not raw_docs:
        print("Error: No documents found in data/knowledge_base/. Seed some markdown files first.")
        logger.error("No documents found to build vector store.")
        sys.exit(1)

    print(f"Splitting {len(raw_docs)} documents...")
    splitter = MedicalTextSplitter()
    chunks = splitter.split_documents(raw_docs)

    print("Parsing and cleaning chunks...")
    doc_parser = MedicalDocumentParser()
    processed_chunks = doc_parser.parse_sections(chunks)

    print(f"Adding {len(processed_chunks)} chunks to ChromaDB. This may take a moment...")
    success = store.add_documents(processed_chunks)

    if success:
        total_indexed = store.get_document_count()
        print("\n=== Indexing Statistics ===")
        print(f"Successfully built vector store!")
        print(f"Chroma DB Path: {store.persist_dir}")
        print(f"Total Document Chunks: {total_indexed}")
        print("===========================")
        logger.info(f"Vector store built successfully with {total_indexed} chunks.")
    else:
        print("Error: Indexing documents failed. Check logs for details.")
        logger.error("Vector store build failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
