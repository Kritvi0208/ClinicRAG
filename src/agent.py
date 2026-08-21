import re
from typing import Any, Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from src.config import config
from src.tools import all_tools, bmi_calculator, bmr_calculator, water_calculator, medicine_lookup, symptom_checker
from src.prompts import get_agent_prompt_template
from src.logger import logger
from src.retriever import MedicalRetriever

class MedicalAgent:
    """Orchestrates the tool-calling clinical agent with multi-model fallback and local clinical resilience."""
    
    def __init__(self):
        self._llm_cache: Dict[str, ChatGoogleGenerativeAI] = {}

    def get_llm(self, model_name: str) -> ChatGoogleGenerativeAI:
        """Lazy-loads and caches ChatGoogleGenerativeAI for a specific model name."""
        if model_name in self._llm_cache:
            return self._llm_cache[model_name]
            
        if not config.GOOGLE_API_KEY:
            logger.error("Missing GOOGLE_API_KEY during LLM initialization.")
            raise ValueError("GOOGLE_API_KEY is not configured. Please add it to your .env file.")
            
        logger.info(f"Initializing ChatGoogleGenerativeAI: {model_name} (temp={config.TEMPERATURE})")
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=config.TEMPERATURE,
            google_api_key=config.GOOGLE_API_KEY,
            streaming=True
        )
        self._llm_cache[model_name] = llm
        return llm

    def get_executor(self, model_name: str, patient_profile_str: str = "") -> AgentExecutor:
        """Constructs an AgentExecutor dynamically for a specific model and patient profile context."""
        llm = self.get_llm(model_name)
        prompt = get_agent_prompt_template(patient_profile_str)
        
        agent = create_tool_calling_agent(llm, all_tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=all_tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        return executor

    def _try_local_clinical_fallback(self, user_input: str, chat_history: List[Any], patient_profile_str: str) -> Optional[str]:
        """Deterministic local fallback when remote LLM quotas are exhausted."""
        input_lower = user_input.lower().strip()
        
        # 1. Check if user is answering a BMI / metric prompt (e.g. "65 kg and 5'4 height")
        weight = None
        kg_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilos|kilograms)", input_lower)
        if kg_match:
            weight = float(kg_match.group(1))
        else:
            lbs_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lbs|pounds|lb)", input_lower)
            if lbs_match:
                weight = float(lbs_match.group(1)) * 0.453592
                
        height_cm = None
        ft_in_match = re.search(r"(\d+)\s*(?:'|ft|feet)\s*(\d+(?:\.\d+)?)?\s*(?:\"|in|inches)?", input_lower)
        if ft_in_match:
            feet = float(ft_in_match.group(1))
            inches = float(ft_in_match.group(2)) if ft_in_match.group(2) else 0.0
            height_cm = ((feet * 12) + inches) * 2.54
        else:
            cm_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|centimeters)", input_lower)
            if cm_match:
                height_cm = float(cm_match.group(1))
                
        if weight and height_cm:
            bmi_res = bmi_calculator.invoke({"weight_kg": weight, "height_cm": height_cm})
            return (
                f"### Body Mass Index (BMI) Assessment\n\n"
                f"**Calculated from inputs**: Weight = {weight:.1f} kg | Height = {height_cm:.1f} cm\n\n"
                f"{bmi_res}\n\n"
                f"Suggested Follow-ups:\n"
                f"1. How can I maintain a healthy BMI?\n"
                f"2. Daily calorie requirement for this weight\n"
                f"3. Recommended water intake"
            )

        # 2. Check for medication lookups (e.g. "paracetamol", "aspirin", "ibuprofen")
        med_words = ["paracetamol", "aspirin", "ibuprofen", "metformin", "amoxicillin", "atorvastatin", "omeprazole", "lisinopril"]
        for med in med_words:
            if med in input_lower:
                med_res = medicine_lookup.invoke(med)
                return (
                    f"{med_res}\n\n"
                    f"Suggested Follow-ups:\n"
                    f"1. Common side effects of {med.capitalize()}\n"
                    f"2. Check drug interactions with {med.capitalize()}\n"
                    f"3. Storage guidelines for {med.capitalize()}"
                )

        # 3. Direct RAG Retrieval from local knowledge base (WHO, MedlinePlus)
        try:
            retriever = MedicalRetriever()
            docs = retriever.retrieve(user_input)
            if docs:
                import streamlit as st
                st.session_state["last_retrieved_docs"] = docs
                
                content_snippets = "\n\n".join([f"• **{d.metadata.get('source_name', 'Clinical Reference')}** ({d.metadata.get('section', 'General')}):\n{d.page_content.strip()}" for d in docs[:2]])
                return (
                    f"### Clinical Decision Support Overview\n\n"
                    f"{content_snippets}\n\n"
                    f"**Guidance**: If symptoms persist or worsen, please consult a healthcare professional.\n\n"
                    f"Suggested Follow-ups:\n"
                    f"1. Common warning signs to monitor\n"
                    f"2. Recommended lifestyle adjustments\n"
                    f"3. When to seek immediate care"
                )
        except Exception as e:
            logger.warning(f"Local RAG fallback retrieval error: {e}")
            
        return None

    def run(self, user_input: str, chat_history: List[Any], patient_profile_str: str = "") -> Dict[str, Any]:
        """Invokes agent executor with multi-model fallback cascade."""
        models_to_try = [config.LLM_MODEL_NAME] + [m for m in config.FALLBACK_MODELS if m != config.LLM_MODEL_NAME]
        
        last_error = ""
        for model_idx, model_name in enumerate(models_to_try):
            try:
                logger.info(f"Attempting execution with model ({model_idx+1}/{len(models_to_try)}): {model_name}")
                executor = self.get_executor(model_name, patient_profile_str)
                
                response = executor.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                })
                
                output_val = response.get("output", "")
                if isinstance(output_val, list):
                    text_parts = []
                    for part in output_val:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif isinstance(part, dict):
                            text_parts.append(part.get("text", ""))
                        elif hasattr(part, "text"):
                            text_parts.append(part.text)
                        else:
                            text_parts.append(str(part))
                    response["output"] = "".join(text_parts)
                elif not isinstance(output_val, str):
                    response["output"] = str(output_val)
                    
                logger.info(f"Successfully generated response with model: {model_name}")
                return response
                
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                logger.warning(f"Model {model_name} failed: {error_str}")
                
                # Check if error is quota exhaustion / rate limit -> try next fallback model
                is_quota_or_rate_limit = (
                    "RESOURCE_EXHAUSTED" in error_str or 
                    "429" in error_str or 
                    "quota" in error_str.lower() or 
                    "rate limit" in error_str.lower() or
                    "overloaded" in error_str.lower()
                )
                
                if is_quota_or_rate_limit:
                    logger.info(f"Model {model_name} hit quota limit. Cascading to next fallback model...")
                    continue
                else:
                    # Non-quota error, try next model just in case
                    continue
                    
        # If all remote models were exhausted, use local deterministic clinical engine
        logger.info("All remote LLM models exhausted. Executing local clinical fallback engine...")
        local_output = self._try_local_clinical_fallback(user_input, chat_history, patient_profile_str)
        if local_output:
            return {
                "output": local_output,
                "intermediate_steps": []
            }
            
        # Safe, polite clinical message if local engine could not resolve
        return {
            "output": (
                "### Clinical Decision Support\n\n"
                "I am currently operating in high-resilience offline mode. "
                "Please specify your symptoms, medication name (e.g. Paracetamol, Ibuprofen), or health metrics "
                "(e.g. '65 kg and 165 cm height' for BMI) so I can retrieve verified guidelines directly from our medical database."
            ),
            "intermediate_steps": []
        }