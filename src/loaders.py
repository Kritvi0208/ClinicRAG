import os
from pathlib import Path
from typing import List, Generator
from langchain_core.documents import Document
from src.logger import logger

class MedicalDocumentLoader:
    """Recursively loads Markdown and Text documents from the medical knowledge base."""
    
    def __init__(self, directory_path: Path):
        self.directory_path = Path(directory_path)
        
    def _get_files(self) -> Generator[Path, None, None]:
        """Generator that yields valid Markdown and Text files in the directory."""
        if not self.directory_path.exists():
            logger.warning(f"Knowledge base directory {self.directory_path} does not exist.")
            return
            
        for root, _, files in os.walk(self.directory_path):
            for file in files:
                file_path = Path(root) / file
                # Ignore hidden, empty, or system files
                if file.startswith('.') or file_path.stat().st_size == 0:
                    continue
                # Support Markdown, text, and PDF files
                if file_path.suffix.lower() in ['.md', '.txt', '.pdf']:
                    yield file_path

    def load(self) -> List[Document]:
        """Loads all documents from the source folder into LangChain Document objects."""
        documents = []
        for file_path in self._get_files():
            try:
                # Read content based on file type
                if file_path.suffix.lower() == '.pdf':
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    text_parts = []
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    content = "\n\n".join(text_parts)
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                
                # Determine document attributes based on directory structure
                relative_path = file_path.relative_to(self.directory_path)
                parts = relative_path.parts
                
                # If nested in a subfolder (e.g., Symptoms/fever.md), parts[0] is the category
                category = parts[0] if len(parts) > 1 else "General"
                doc_name = file_path.name
                
                # Determine basic section headers
                section = "Introduction"
                for line in content.splitlines():
                    if line.startswith("# "):
                        section = line.replace("#", "").strip()
                        break
                    elif line.startswith("## "):
                        section = line.replace("##", "").strip()
                        break
                
                # Build metadata dictionary
                metadata = {
                    "source": str(file_path),
                    "source_name": doc_name,
                    "category": category,
                    "section": section,
                    "file_size": file_path.stat().st_size
                }
                
                documents.append(Document(page_content=content, metadata=metadata))
            except Exception as e:
                logger.error(f"Failed to load document {file_path}: {e}")
                
        logger.info(f"Loaded {len(documents)} documents from {self.directory_path}.")
        return documents
