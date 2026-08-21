import json
import time
import re
from pathlib import Path
from typing import Any, Dict, List
from src.logger import logger

def clean_text(text: str) -> str:
    """Cleans raw text by removing excessive whitespaces and formatting issues."""
    if not text:
        return ""
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text)
    # Remove HTML tags if any
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()

def format_sources(docs: List[Any]) -> str:
    """Formats retrieved document metadata into a clean markdown structure."""
    if not docs:
        return "No external sources used."
        
    formatted = "### Sources Used:\n"
    seen_sources = set()
    
    for idx, doc in enumerate(docs):
        meta = getattr(doc, "metadata", {})
        source_name = meta.get("source_name", "Unknown File")
        category = meta.get("category", "General")
        section = meta.get("section", "General Reference")
        
        # Unique identifier to prevent duplicate source output
        source_key = f"{source_name} - {section}"
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        
        snippet = doc.page_content[:150].replace('\n', ' ') + "..."
        formatted += f"- **Source {idx+1}**: {source_name} (Category: `{category}`, Section: `{section}`)\n"
        formatted += f"  - *Snippet*: \"{snippet}\"\n"
        
    return formatted

def time_formatter(seconds: float) -> str:
    """Formats a float representing seconds into a human-readable duration."""
    if seconds < 1.0:
        return f"{seconds * 1000:.2f} ms"
    return f"{seconds:.2f} seconds"

def token_counter(text: str) -> int:
    """Estimates the number of tokens in the given text using standard word boundaries."""
    if not text:
        return 0
    # Standard heuristic: 1 token ~= 4 characters or 0.75 words
    words = len(text.split())
    return int(words * 1.33) + 1

def exception_formatter(e: Exception) -> str:
    """Extracts a readable message from exceptions without tracebacks."""
    name = type(e).__name__
    message = str(e)
    return f"[{name}] {message}"

def load_json(filepath: Path) -> Dict[str, Any]:
    """Helper to safely read a JSON database file."""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON from {filepath}: {e}")
        return {}

def save_json(data: Dict[str, Any], filepath: Path) -> bool:
    """Helper to safely save a JSON database file."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON to {filepath}: {e}")
        return False
