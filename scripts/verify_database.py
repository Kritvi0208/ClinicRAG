import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.vector_store import MedicalVectorStore
from src.retriever import MedicalRetriever
from src.logger import logger

def main():
    print("Verifying ClinicRAG Database Status...")
    store = MedicalVectorStore()
    
    try:
        doc_count = store.get_document_count()
        db = store.get_db()
        print(f"Connection successful!")
        print(f"Persistent Directory: {store.persist_dir}")
        print(f"Total Document Chunks: {doc_count}")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Get distinct source names
    sources = set()
    try:
        results = db._collection.get(include=["metadatas"])
        if results and "metadatas" in results:
            for meta in results["metadatas"]:
                if meta and "source_name" in meta:
                    sources.add(meta["source_name"])
        print(f"Unique source files indexed ({len(sources)}):")
        for idx, src in enumerate(sorted(sources)):
            print(f"  {idx+1}. {src}")
    except Exception as e:
        print(f"Failed to query indexed source names: {e}")

    # Test retriever response time
    if doc_count > 0:
        test_query = "What are the emergency signs of a heart attack?"
        print(f"\nRunning test retrieval query: '{test_query}'...")
        retriever = MedicalRetriever(store)
        
        start_time = time.time()
        docs = retriever.retrieve(test_query, top_k=2)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Retrieval complete in {duration:.4f} seconds.")
        print(f"Retrieved {len(docs)} relevant chunks.")
        
        if docs:
            print("\nFirst retrieved chunk preview:")
            print(f"  Source: {docs[0].metadata.get('source_name')} - Section: {docs[0].metadata.get('section')}")
            print(f"  Snippet: {docs[0].page_content[:150]}...")
        else:
            print("Warning: No matching chunks found. Database might not be seeded properly.")
    else:
        print("\nDatabase is empty. No query tests can be executed.")

if __name__ == "__main__":
    main()
