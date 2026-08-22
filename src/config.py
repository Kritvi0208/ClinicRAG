import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """Centralized configuration class for ClinicRAG."""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
    PROCESSED_DIR = DATA_DIR / "processed"
    RAW_DIR = DATA_DIR / "raw"
    CHROMA_DB_DIR = BASE_DIR / "chroma_db"
    
    # Ensure dirs exist
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # API configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    if not GOOGLE_API_KEY:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
                GOOGLE_API_KEY = str(st.secrets["GOOGLE_API_KEY"]).strip()
                os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
        except Exception:
            pass
    
    # Model configuration
    LLM_MODEL_NAME = "gemini-3.7-flash"  # Default primary Gemini model
    FALLBACK_MODELS = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest"
    ]
    EMBEDDING_MODEL_NAME = "models/gemini-embedding-001"  # Default Google embedding model
    TEMPERATURE = 0.2
    
    # Retriever parameters
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVER_TOP_K = 4
    SIMILARITY_THRESHOLD = 0.5  # Filter out very low confidence scores
    
    # Memory config
    MAX_CHAT_HISTORY = 10  # Maximum number of conversations stored
    
    # Application settings
    APP_TITLE = "ClinicRAG"
    LOG_FILE = str(BASE_DIR / "clinicrag.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Theme configuration (Pastel Light Purplish Theme)
    COLOR_BG = "#FAF9FD"
    COLOR_ACCENT = "#8B7BC8"
    COLOR_TEXT = "#2E2842"
    COLOR_MUTED = "#6E6685"
    COLOR_CARD = "#FFFFFF"
    
    # Static Data Path
    MEDICINES_DB_PATH = PROCESSED_DIR / "medicines_db.json"
    INTERACTIONS_DB_PATH = PROCESSED_DIR / "interactions_db.json"
    
    # Disclaimer text
    DISCLAIMER = (
        "This information is for educational purposes only and should not replace advice from a "
        "qualified healthcare professional. Seek immediate medical attention for emergencies."
    )

# Instantiate a global config object
config = AppConfig()
