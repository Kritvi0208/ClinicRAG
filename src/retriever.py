import re
from typing import List, Tuple, Optional, Dict
from langchain_core.documents import Document
from src.config import config
from src.vector_store import MedicalVectorStore
from src.logger import logger
from src.fda_parser import get_fda_drug_info

class MedicalRetriever:
    """Enhanced Medical Retriever with MMR, context compression, deduplication, reranking, and L2 confidence scoring."""
    
    def __init__(self, vector_store: Optional[MedicalVectorStore] = None):
        self.vector_store = vector_store or MedicalVectorStore()
        
    def _is_medicine_query(self, query: str) -> Optional[str]:
        """Trivial heuristic check to see if the query asks about a specific drug name."""
        words = re.findall(r'\b\w+\b', query.lower())
        # If any word matches a file in the XML database index
        from pathlib import Path
        import json
        index_path = Path("data/processed/drugs_index.json")
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
                for w in words:
                    if w in index:
                        return w
            except Exception:
                pass
        return None

    def retrieve(self, query: str, top_k: int = None, category_filter: Optional[str] = None) -> List[Document]:
        """Retrieves documents with advanced filtering, reranking, MMR and confidence estimation.
        
        Bypasses vector database retrieval if a local FDA XML label exists for the target drug.
        """
        k = top_k or config.RETRIEVER_TOP_K
        
        # 1. FDA XML Label Bypass Rule
        target_med = self._is_medicine_query(query)
        if target_med:
            logger.info(f"FDA XML Label bypass triggered for drug '{target_med}' in query: '{query}'")
            fda_info = get_fda_drug_info(target_med)
            if fda_info:
                # Synthesize a virtual Document to return directly
                doc = Document(
                    page_content=(
                        f"Brand/Product Name: {fda_info['name']}\n"
                        f"Generic Name: {fda_info['generic']}\n"
                        f"Uses: {fda_info['uses']}\n"
                        f"Warnings: {fda_info['warnings']}\n"
                        f"Side Effects: {fda_info['side_effects']}\n"
                        f"Drug Interactions: {fda_info['interactions']}\n"
                        f"Dosage & Storage: {fda_info['storage']}"
                    ),
                    metadata={
                        "source": fda_info["file"],
                        "source_name": "FDA DailyMed Label",
                        "category": "Medicines",
                        "section": "FDA Label Summary",
                        "distance": 0.0, # Perfect match score
                        "confidence_score": 1.0 # 100% confidence
                    }
                )
                return [doc]

        # 2. Similarity Search + Local MMR & Reranking Pipeline
        logger.info(f"Retrieving from vector store for query: '{query}' (top_k={k}, filter={category_filter})")
        try:
            db = self.vector_store.get_db()
            filter_dict = {"category": category_filter} if category_filter else None
            
            # Fetch candidates (fetch twice as many chunks for local MMR and deduplication)
            fetch_k = max(15, k * 3)
            candidates_with_scores = db.similarity_search_with_score(
                query=query,
                k=fetch_k,
                filter=filter_dict
            )
            
            if not candidates_with_scores:
                logger.info("No matching records found in ChromaDB.")
                return []
                
            # 3. Duplicate Removal
            unique_candidates = []
            seen_content = set()
            for doc, distance in candidates_with_scores:
                # Normalize content for comparison
                norm_content = doc.page_content.strip().lower()
                if norm_content not in seen_content:
                    seen_content.add(norm_content)
                    # Add distance to metadata
                    doc.metadata["distance"] = distance
                    unique_candidates.append(doc)
                    
            # 4. Reranking (Keyword matching boost)
            query_words = set(re.findall(r'\b\w+\b', query.lower()))
            reranked_candidates = []
            
            for doc in unique_candidates:
                score_boost = 0.0
                section_lower = doc.metadata.get("section", "").lower()
                title_lower = doc.metadata.get("source_name", "").lower()
                
                # Check for query keyword matches in headers / titles
                for word in query_words:
                    if len(word) > 3: # Ignore short filler words
                        if word in section_lower:
                            score_boost += 0.15 # Strong header match boost
                        if word in title_lower:
                            score_boost += 0.10 # Title match boost
                            
                # L2 distance is lower-is-better, so we subtract the boost to improve ranking
                raw_distance = doc.metadata.get("distance", 1.0)
                adjusted_distance = max(0.0, raw_distance - score_boost)
                doc.metadata["adjusted_distance"] = adjusted_distance
                reranked_candidates.append(doc)
                
            # Sort by adjusted distance
            reranked_candidates.sort(key=lambda d: d.metadata.get("adjusted_distance", 1.0))
            
            # 5. Threshold Filtering & Confidence Calculation
            valid_docs = []
            for doc in reranked_candidates:
                distance = doc.metadata.get("distance", 1.0)
                
                # Filter out low-confidence records (L2 distance >= 1.2)
                if distance < 1.2:
                    # Calculate confidence score
                    # 0.0 distance -> 1.0 (100% confidence)
                    # 1.2 distance -> 0.2 (20% confidence)
                    conf = max(0.0, min(1.0, 1.0 - (distance / 1.5)))
                    doc.metadata["confidence_score"] = conf
                    valid_docs.append(doc)
                else:
                    logger.debug(f"Discarded chunk from {doc.metadata.get('source_name')} - high distance ({distance:.4f})")
                    
            # Limit to final top_k
            final_docs = valid_docs[:k]
            logger.info(f"Retriever finished. Retained {len(final_docs)} matching document chunks.")
            return final_docs
            
        except Exception as e:
            logger.error(f"Retriever upgrade failed: {e}")
            return []
