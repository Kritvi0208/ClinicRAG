import queue
import re
import threading
import time
from typing import Any, Dict, Generator, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from src.config import config
from src.tools import all_tools, bmi_calculator, bmr_calculator, water_calculator, medicine_lookup, symptom_checker
from src.prompts import get_agent_prompt_template
from src.logger import logger
from src.retriever import MedicalRetriever

def extract_token_text(token_content: Any) -> str:
    """Safely extracts string token from str, list, dict, or object chunks."""
    if isinstance(token_content, str):
        return token_content
    if isinstance(token_content, list):
        parts = []
        for p in token_content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict):
                parts.append(p.get("text", ""))
            elif hasattr(p, "text"):
                parts.append(getattr(p, "text", ""))
            else:
                parts.append(str(p))
        return "".join(parts)
    if isinstance(token_content, dict):
        return token_content.get("text", str(token_content))
    if hasattr(token_content, "text"):
        return getattr(token_content, "text", "")
    return str(token_content)

class TokenStreamCallbackHandler(BaseCallbackHandler):
    """Captures real-time token generation and tool lifecycle events."""
    def __init__(self, token_queue: queue.Queue):
        self.queue = token_queue
        self.in_tool = False

    def on_llm_new_token(self, token: Any, **kwargs) -> None:
        text = extract_token_text(token)
        if text:
            self.queue.put({"type": "token", "content": text})

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        self.in_tool = True
        tool_name = serialized.get("name", "Clinical Tool")
        self.queue.put({"type": "tool_start", "name": tool_name, "input": input_str})

    def on_tool_end(self, output: str, **kwargs) -> None:
        self.in_tool = False
        self.queue.put({"type": "tool_end", "output": output})

    def on_tool_error(self, error: BaseException, **kwargs) -> None:
        self.in_tool = False
        self.queue.put({"type": "tool_error", "error": str(error)})

    def on_llm_error(self, error: BaseException, **kwargs) -> None:
        self.queue.put({"type": "llm_error", "error": str(error)})

# Model cooldown tracker to immediately skip rate-limited models on subsequent queries
_model_cooldowns: Dict[str, float] = {}

def get_ordered_models() -> List[str]:
    """Returns candidate models prioritizing healthy models over those currently in rate-limit cooldown."""
    all_models = [config.LLM_MODEL_NAME] + [m for m in config.FALLBACK_MODELS if m != config.LLM_MODEL_NAME]
    now = time.time()
    active = [m for m in all_models if _model_cooldowns.get(m, 0) <= now]
    cooling = [m for m in all_models if _model_cooldowns.get(m, 0) > now]
    return active + cooling

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
            streaming=True,
            max_retries=0
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
                f"Suggested Follow-up Questions:\n"
                f"1. How can I maintain a healthy BMI through diet?\n"
                f"2. What is my daily calorie requirement for this weight?\n"
                f"3. How much water should I drink daily?"
            )

        # 2. Check for medication lookups (e.g. "paracetamol", "aspirin", "ibuprofen")
        med_words = ["paracetamol", "aspirin", "ibuprofen", "metformin", "amoxicillin", "atorvastatin", "omeprazole", "lisinopril"]
        for med in med_words:
            if med in input_lower:
                med_res = medicine_lookup.invoke(med)
                return (
                    f"{med_res}\n\n"
                    f"Suggested Follow-up Questions:\n"
                    f"1. What are common side effects of {med.capitalize()}?\n"
                    f"2. Can you check drug interactions with {med.capitalize()}?\n"
                    f"3. What are the proper storage guidelines for {med.capitalize()}?"
                )

        # 3. Direct RAG Retrieval from local knowledge base (WHO, MedlinePlus)
        try:
            retriever = MedicalRetriever()
            docs = retriever.retrieve(user_input)
            if docs:
                from src.tools import _safe_set_state
                _safe_set_state("last_retrieved_docs", docs)
                
                content_snippets = "\n\n".join([f"• **{d.metadata.get('source_name', 'Clinical Reference')}** ({d.metadata.get('section', 'General')}):\n{d.page_content.strip()}" for d in docs[:2]])
                return (
                    f"### Clinical Decision Support Overview\n\n"
                    f"{content_snippets}\n\n"
                    f"**Guidance**: If symptoms persist or worsen, please consult a healthcare professional.\n\n"
                    f"Suggested Follow-up Questions:\n"
                    f"1. What warning signs should I monitor?\n"
                    f"2. What lifestyle adjustments do you recommend?\n"
                    f"3. When should I seek immediate medical care?"
                )
        except Exception as e:
            logger.warning(f"Local RAG fallback retrieval error: {e}")
            
        return None

    def stream_run(
        self, 
        user_input: str, 
        chat_history: List[Any], 
        patient_profile_str: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """Streams LLM tokens in real-time as they are produced by Google Gemini.
        
        Yields:
            Dict events with types:
            - 'token': Incremental generated token string
            - 'tool_start': Tool execution notice with tool name
            - 'tool_end': Tool execution completion
            - 'final_result': Complete dictionary containing final output and metadata
            - 'error': Generation error message if failure occurs
        """
        token_queue = queue.Queue()
        callback = TokenStreamCallbackHandler(token_queue)
        result_holder = {}

        def _worker_thread():
            models_to_try = get_ordered_models()
            
            for model_idx, model_name in enumerate(models_to_try):
                try:
                    logger.info(f"Streaming execution with model ({model_idx+1}/{len(models_to_try)}): {model_name}")
                    executor = self.get_executor(model_name, patient_profile_str)
                    
                    response = executor.invoke(
                        {"input": user_input, "chat_history": chat_history},
                        config={"callbacks": [callback]}
                    )
                    
                    output_val = response.get("output", "")
                    response["output"] = extract_token_text(output_val)
                    result_holder["response"] = response
                    _model_cooldowns.pop(model_name, None)
                    logger.info(f"Stream generation finished successfully with model: {model_name}")
                    return
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        _model_cooldowns[model_name] = time.time() + 60.0
                        logger.info(f"Model {model_name} rate limited (429). Setting 60s circuit-breaker cooldown.")
                    elif "503" in error_str or "UNAVAILABLE" in error_str:
                        _model_cooldowns[model_name] = time.time() + 30.0
                    logger.warning(f"Streaming model {model_name} failed: {error_str}")
                    continue
                    
            # Fallback to local clinical engine
            logger.info("Remote models failed during streaming. Executing local clinical engine...")
            local_out = self._try_local_clinical_fallback(user_input, chat_history, patient_profile_str)
            if local_out:
                result_holder["response"] = {"output": local_out, "intermediate_steps": []}
            else:
                result_holder["response"] = {
                    "output": (
                        "### Clinical Decision Support\n\n"
                        "I am currently operating in high-resilience offline mode. "
                        "Please specify your symptoms, medication name (e.g. Paracetamol, Ibuprofen), or health metrics "
                        "(e.g. '65 kg and 165 cm height' for BMI) so I can retrieve verified guidelines directly from our medical database."
                    ),
                    "intermediate_steps": []
                }
            
            # Emit words from local fallback
            if "response" in result_holder:
                for word in result_holder["response"]["output"].split(" "):
                    token_queue.put({"type": "token", "content": word + " "})
                    time.sleep(0.015)

        worker = threading.Thread(target=_worker_thread, daemon=True)
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx
            add_script_run_ctx(worker)
        except Exception:
            pass
        worker.start()

        while worker.is_alive() or not token_queue.empty():
            try:
                event = token_queue.get(timeout=0.05)
                yield event
            except queue.Empty:
                continue

        worker.join(timeout=1.0)

        if "response" in result_holder:
            yield {"type": "final_result", "result": result_holder["response"]}
        elif "error" in result_holder:
            yield {"type": "error", "error": result_holder["error"]}

    def run(self, user_input: str, chat_history: List[Any], patient_profile_str: str = "") -> Dict[str, Any]:
        """Invokes agent executor with multi-model fallback cascade."""
        models_to_try = get_ordered_models()
        
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
                response["output"] = extract_token_text(output_val)
                _model_cooldowns.pop(model_name, None)
                    
                logger.info(f"Successfully generated response with model: {model_name}")
                return response
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    _model_cooldowns[model_name] = time.time() + 60.0
                elif "503" in error_str or "UNAVAILABLE" in error_str:
                    _model_cooldowns[model_name] = time.time() + 30.0
                last_error = error_str
                logger.warning(f"Model {model_name} failed: {error_str}")
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