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
                
        # 4. LLM-based structured intent routing for complex clinical queries
        models_to_try = [config.LLM_MODEL_NAME] + [m for m in config.FALLBACK_MODELS if m != config.LLM_MODEL_NAME]
        
        for model_name in models_to_try:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0.0,
                    google_api_key=config.GOOGLE_API_KEY
                )
        
                system_prompt = (
                    "You are an intelligent medical intent router.\n"
                    f"Classify the user's query into one or more of the following intents: {self.SUPPORTED_INTENTS}.\n\n"
                    "Query context may include the previous conversation history if provided.\n"
                    "Provide the response strictly in JSON format matching this schema:\n"
                    "{\n"
                    "  \"intents\": [\"Intent1\", \"Intent2\"]\n"
                    "}\n\n"
                    "If the query involves severe emergency indicators like chest pain, severe bleeding, stroke signs, poisoning, seizures, "
                    "or suicidal ideation, you MUST include 'Emergency' in the intents list."
                )
                
                user_prompt = f"User Query: {query}\nHistory:\n{history_str}"
                
                messages = [
                    ("system", system_prompt),
                    ("human", user_prompt)
                ]
                
                response = llm.invoke(messages)
                response_text = response.content.strip() if isinstance(response.content, str) else str(response.content)
                
                if response_text.startswith("```"):
                    lines = response_text.splitlines()
                    if len(lines) > 2:
                        response_text = "\n".join(lines[1:-1])
                
                data = json.loads(response_text)
                intents = data.get("intents", ["General Health"])
                
                valid_intents = [i for i in intents if i in self.SUPPORTED_INTENTS]
                if not valid_intents:
                    valid_intents = ["General Health"]
                    
                emergency_bypass = "Emergency" in valid_intents
                
                logger.info(f"Intent Router results ({model_name}): intents={valid_intents}, emergency_bypass={emergency_bypass}")
                return {
                    "intents": valid_intents,
                    "emergency_bypass": emergency_bypass,
                    "matched_flag": None
                }
                
            except Exception as e:
                logger.warning(f"Intent Router model {model_name} failed: {e}. Trying next fallback...")
                continue
                
        # Final safe rule-based fallback if all router models failed
        is_emergency = "emergency" in query_lower or "cpr" in query_lower or "choking" in query_lower or "bleeding" in query_lower
        return {
            "intents": ["Emergency"] if is_emergency else ["General Health"],
            "emergency_bypass": is_emergency,
            "matched_flag": None
        }
