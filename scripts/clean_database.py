import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.vector_store import MedicalVectorStore
from src.logger import logger

def main():
    print("WARNING: This will wipe the persistent ChromaDB collection.")
    confirm = input("Are you sure you want to proceed? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Operation cancelled.")
        return
        
    store = MedicalVectorStore()
    print(f"Cleaning database at {store.persist_dir}...")
    success = store.clean_database()
    
    if success:
        print("Database wiped successfully.")
        logger.info("ChromaDB wiped successfully.")
    else:
        print("Error: Failed to wipe database.")
        sys.exit(1)

if __name__ == "__main__":
    main()
