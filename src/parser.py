import re
from typing import List
from langchain_core.documents import Document
from src.logger import logger

class MedicalDocumentParser:
    """Parses text chunks to refine section metadata and clean up markdown syntax."""
    
    @staticmethod
    def clean_chunk_text(text: str) -> str:
        """Cleans formatting or syntax issues from a chunk."""
        # Remove empty lines, normalize multiple spaces
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def parse_sections(self, chunks: List[Document]) -> List[Document]:
        """Iterates through chunks and detects section headings to refine chunk metadata."""
        parsed_chunks = []
        for chunk in chunks:
            content = chunk.page_content
            # Look for headers in this specific chunk content
            headers = re.findall(r'^(?:#|##|###)\s+(.+)$', content, re.MULTILINE)
            
            # If a header is found inside this chunk, update metadata to match it
            if headers:
                chunk.metadata["section"] = headers[0].strip()
            
            # Clean page content
            chunk.page_content = self.clean_chunk_text(content)
            parsed_chunks.append(chunk)
            
        return parsed_chunks
