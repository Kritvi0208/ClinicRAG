import streamlit as st
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from src.config import config
from src.logger import logger

class MedicalMemory:
    """Manages conversation chat history and maintains structured patient profile memory."""
    
    def __init__(self, session_key: str = "chat_messages", profile_key: str = "patient_profile"):
        self.session_key = session_key
        self.profile_key = profile_key
        
        # Initialize message history
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []
            logger.info("Initializing chat message session state memory.")
            
        # Initialize patient profile
        if self.profile_key not in st.session_state:
            st.session_state[self.profile_key] = {
                "age": "",
                "gender": "",
                "known_diseases": "",
                "current_medicines": "",
                "allergies": "",
                "pregnancy": "No",
                "previous_symptoms": "",
                "notes": ""
            }
            logger.info("Initializing patient profile session state memory.")

    def add_message(self, role: str, content: str) -> None:
        """Adds a message to the memory buffer."""
        st.session_state[self.session_key].append({"role": role, "content": content})
        logger.info(f"Memory added: {role} -> {content[:50]}...")
        self._truncate_memory()

    def get_messages(self) -> List[Dict[str, str]]:
        """Returns all messages currently stored."""
        return st.session_state[self.session_key]

    def clear(self) -> None:
        """Clears message history and resets session counters."""
        st.session_state[self.session_key] = []
        logger.info("Chat history cleared from memory.")
        
    def clear_all(self) -> None:
        """Resets both message history and patient profile."""
        self.clear()
        st.session_state[self.profile_key] = {
            "age": "",
            "gender": "",
            "known_diseases": "",
            "current_medicines": "",
            "allergies": "",
            "pregnancy": "No",
            "previous_symptoms": "",
            "notes": ""
        }
        logger.info("Chat history and patient profile fully reset.")

    def _truncate_memory(self) -> None:
        """Truncates the message history to the maximum allowed length (configurable)."""
        history = st.session_state[self.session_key]
        max_len = config.MAX_CHAT_HISTORY * 2
        if len(history) > max_len:
            truncated = history[-max_len:]
            st.session_state[self.session_key] = truncated
            logger.info(f"Truncated memory. Retained last {max_len} messages.")

    def get_langchain_messages(self) -> List[BaseMessage]:
        """Converts the internal messages dictionary into LangChain BaseMessage objects."""
        messages: List[BaseMessage] = []
        for msg in st.session_state[self.session_key]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages

    def get_formatted_history_string(self) -> str:
        """Formats the chat history as a flat text block for prompt injection."""
        formatted = ""
        for msg in st.session_state[self.session_key]:
            role_label = "Patient" if msg["role"] == "user" else "Assistant"
            formatted += f"{role_label}: {msg['content']}\n"
        return formatted

    # Structured Patient Profile Memory methods
    def get_patient_profile(self) -> Dict[str, Any]:
        """Retrieves the active patient profile dictionary."""
        return st.session_state[self.profile_key]

    def update_patient_profile(self, profile_dict: Dict[str, Any]) -> None:
        """Updates the active patient profile with new values."""
        st.session_state[self.profile_key].update(profile_dict)
        logger.info("Patient profile memory updated.")

    def get_patient_profile_string(self) -> str:
        """Formats the patient profile into a clear markdown header block for prompt context."""
        p = st.session_state[self.profile_key]
        lines = []
        if p.get("age"):
            lines.append(f"- **Age**: {p['age']}")
        if p.get("gender"):
            lines.append(f"- **Gender**: {p['gender']}")
        if p.get("pregnancy") and p["pregnancy"] != "No":
            lines.append(f"- **Pregnancy Status**: {p['pregnancy']}")
        if p.get("allergies"):
            lines.append(f"- **Allergies**: {p['allergies']}")
        if p.get("known_diseases"):
            lines.append(f"- **Known Diseases**: {p['known_diseases']}")
        if p.get("current_medicines"):
            lines.append(f"- **Current Medications**: {p['current_medicines']}")
        if p.get("previous_symptoms"):
            lines.append(f"- **Previous/Chronic Symptoms**: {p['previous_symptoms']}")
            
        if lines:
            return "\n### ACTIVE PATIENT PROFILE:\n" + "\n".join(lines) + "\n\n"
        return ""
