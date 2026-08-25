import json
import re
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import config
from src.logger import logger

class IntentRouter:
    """Classifies user queries into health categories and flags emergency situations."""
    
    SUPPORTED_INTENTS = [
        "Disease", "Symptoms", "Medicine Information", "Drug Interaction", 
        "Side Effects", "Dosage", "Pregnancy", "Mental Health", "Nutrition", 
        "Emergency", "First Aid", "Lifestyle", "Calculator", "General Health", 
        "Follow-up Conversation", "Greeting"
    ]
    
    # Red flags for instant rule-based emergency safety bypass
    EMERGENCY_RED_FLAGS = [
        "chest pain", "heart attack", "difficulty breathing", "shortness of breath",
        "loss of consciousness", "unresponsive", "stroke", "slurred speech",
        "face drooping", "arm weakness", "severe allergic reaction", "anaphylaxis",
        "poisoning", "swallowed poison", "seizure", "seizures", "suicidal", "kill myself",
        "severe bleeding", "heavy bleeding", "bleeding heavily", "coughing blood",
        "uncontrolled bleeding", "head trauma", "severe burn"
    ]
    
    def __init__(self):
        self._llm = None
        
    def _get_llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=config.LLM_MODEL_NAME,
                temperature=0.0,
                google_api_key=config.GOOGLE_API_KEY
            )
        return self._llm

    def classify(self, query: str, history_str: str = "") -> Dict[str, Any]:
        """Classifies query into intents and returns emergency flags.
        
        Returns:
            Dict containing 'intents' (list), 'emergency_bypass' (bool), and 'matched_flag'.
        """
        query_lower = query.lower().strip()
        
        # 1. Rule-based instant safety bypass (Highest Priority)
        for flag in self.EMERGENCY_RED_FLAGS:
            if flag in query_lower:
                logger.info(f"Emergency safety bypass triggered by rule-based flag: '{flag}'")
                return {
                    "intents": ["Emergency", "First Aid"],
                    "emergency_bypass": True,
                    "matched_flag": flag
                }
                
        # 2. Rule-based fast greeting detection (Instant response, 0ms latency)
        greeting_pattern = r"^(hi+|he+y+|hello+|howdy|greetings|good\s+(morning|afternoon|evening)|how\s+are\s+you|what'?s\s+up|sup)\b"
        if re.match(greeting_pattern, query_lower):
            # Check if it's purely a greeting or contains clinical words
            clinical_keywords = ["pain", "symptom", "fever", "cough", "dose", "medicine", "pill", "drug", "blood", "headache", "doctor", "prescribe", "treatment"]
            if not any(k in query_lower for k in clinical_keywords):
                return {
                    "intents": ["Greeting"],
                    "emergency_bypass": False,
                    "matched_flag": None
                }

        # 3. Rule-based fast calculator classification
        if "bmi" in query_lower:
            return {
                "intents": ["Calculator"],
                "calculator": "BMI",
                "emergency_bypass": False,
                "matched_flag": None
            }

        if "bmr" in query_lower:
            return {
                "intents": ["Calculator"],
                "calculator": "BMR",
                "emergency_bypass": False,
                "matched_flag": None
            }

        if "water intake" in query_lower or "how much water" in query_lower:
            return {
                "intents": ["Calculator"],
                "calculator": "Water",
                "emergency_bypass": False,
                "matched_flag": None
            }

        if "calorie" in query_lower or "tdee" in query_lower:
            return {
                "intents": ["Calculator"],
                "calculator": "Calories",
                "emergency_bypass": False,
                "matched_flag": None
            }

        if "convert" in query_lower:
            return {
                "intents": ["Calculator"],
                "calculator": "Converter",
                "emergency_bypass": False,
                "matched_flag": None
            }
                
        # 4. Single-Pass Fast Routing (Eliminates redundant ~2.8s LLM network roundtrip)
        intents = ["General Health"]
        med_indicators = ["medicine", "drug", "pill", "tablet", "dosage", "side effect", "interaction", "contraindication", "mg", "capsule", "prescription"]
        symptom_indicators = ["pain", "fever", "cough", "headache", "ache", "sore", "infection", "vomit", "nausea", "dizziness", "rash", "disease", "treatment", "guideline"]
        
        if any(w in query_lower for w in med_indicators):
            intents.append("Medication")
        if any(w in query_lower for w in symptom_indicators):
            intents.append("Symptoms")
            
        logger.info(f"Single-pass fast routing (0ms): intents={intents}")
        return {
            "intents": intents,
            "emergency_bypass": False,
            "matched_flag": None
        }
