from functools import lru_cache
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import config
from src.logger import logger

@lru_cache(maxsize=1)
def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """Creates and caches the Google Generative AI Embeddings client.
    
    Using @lru_cache guarantees we only instantiate it once across the application lifetime.
    """
    if not config.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY environment variable is missing.")
        raise ValueError("Missing GOOGLE_API_KEY. Please set it in your .env file.")
        
    logger.info(f"Initializing Google Embeddings: {config.EMBEDDING_MODEL_NAME}")
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model=config.EMBEDDING_MODEL_NAME,
            google_api_key=config.GOOGLE_API_KEY
        )
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize Google Embeddings: {e}")
        raise
