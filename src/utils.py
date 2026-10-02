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

def format_user_followup_prompt(text: str) -> str:
    """Transforms follow-up suggestion questions into first-person user prompts/questions."""
    if not text:
        return ""
    p = text.strip()
    # Strip any leading numbers, dots, dashes, or bullet points
    p = re.sub(r"^[\d\.\-\*\•\)\s]+", "", p).strip()
    
    # 1. Direct transformation of Assistant -> User question patterns
    conversions = [
        # "Are you interested in learning (about/more about)..."
        (r"^(?:are you interested in (?:learning (?:about |more about )?|knowing (?:about )?|learning )?)(.*)", r"What are \1"),
        # "Would you like to know (more about/about)..."
        (r"^(?:would you like to (?:know (?:more about |about )?|learn (?:more about |about )?|hear (?:about )?))(.*)", r"Tell me about \1"),
        # "Would you like (me to) calculate/check..."
        (r"^(?:would you like (?:me to )?calculate (?:your )?)(bmi|bmr|calories|water|tdee|intake)(.*)", r"Can you calculate my \1\2?"),
        (r"^(?:would you like (?:me to )?)(check|calculate|explain|recommend|suggest|provide)(.*)", r"Can you \1\2?"),
        (r"^(?:would you like to )(.*)", r"How can I \1?"),
        # "Do you have any specific fitness or wellness goals you are hoping to achieve?"
        (r"^(?:do you have any specific |do you have any )(.*?)(?:\s+you are hoping to achieve|\s+you want to ask|\s+you need assistance with|\s+you would like to discuss)?\??$", r"How can I manage my \1?"),
        # "Do you want to know about..." / "Do you want to..."
        (r"^(?:do you want to know (?:about )?|do you want to learn (?:about )?)(.*)", r"Tell me about \1"),
        (r"^(?:do you want (?:me to )?)(.*)", r"Can you \1?"),
        # "Are you experiencing any other symptoms..."
        (r"^(?:are you experiencing (?:any (?:other )?)?)(.*)", r"What should I do if I have \1?"),
        # "Have you previously had..."
        (r"^(?:have you (?:previously |already )?had (?:a |an )?)(.*)", r"What if I previously had \1?"),
        (r"^(?:have you (?:previously |already )?)(.*)", r"What should I know regarding \1?"),
        # "Can you tell me..." / "Tell me..."
        (r"^(?:please provide |please share )(.*)", r"Can you explain \1?"),
    ]
    
    matched = False
    for pattern, replacement in conversions:
        if re.search(pattern, p, re.IGNORECASE):
            p = re.sub(pattern, replacement, p, flags=re.IGNORECASE).strip()
            matched = True
            break
            
    # 2. Swap second-person pronouns to first-person pronouns if modified
    if matched:
        p = re.sub(r"\byour\b", "my", p, flags=re.IGNORECASE)
        p = re.sub(r"\byours\b", "mine", p, flags=re.IGNORECASE)
        p = re.sub(r"\byou are\b", "I am", p, flags=re.IGNORECASE)
        p = re.sub(r"\byou\b", "me", p, flags=re.IGNORECASE)

    # 3. Clean up formatting
    p = re.sub(r"\s+", " ", p).strip()
    p = re.sub(r"\?+", "?", p)
    if re.match(r"^(?:tell me|suggest|explain|give me)\b", p, re.IGNORECASE) and p.endswith("?"):
        p = p[:-1].strip()
    elif not p.endswith(("?", ".", "!")):
        p = p + "?"
        
    if p:
        p = p[0].upper() + p[1:]
    return p
