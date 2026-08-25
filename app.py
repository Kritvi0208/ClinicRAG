import time
import os
import re
import streamlit as st
from pathlib import Path

# Set Streamlit Page Configuration at the very top
st.set_page_config(
    page_title="ClinicRAG - Clinical Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

import importlib
import src.config
import src.styles
import src.utils
import src.vector_store
import src.fda_parser
import src.prompts
import src.tools
import src.retriever
import src.agent
import src.memory
import src.router

importlib.reload(src.config)
importlib.reload(src.styles)
importlib.reload(src.utils)
importlib.reload(src.vector_store)
importlib.reload(src.fda_parser)
importlib.reload(src.prompts)
importlib.reload(src.tools)
importlib.reload(src.retriever)
importlib.reload(src.agent)
importlib.reload(src.memory)
importlib.reload(src.router)

from src.config import config
from src.logger import logger
from src.styles import apply_custom_css
from src.utils import exception_formatter, token_counter
from src.vector_store import MedicalVectorStore
from src.agent import MedicalAgent
from src.memory import MedicalMemory
from src.router import IntentRouter

# Initialize session state components
if "agent" not in st.session_state:
    st.session_state["agent"] = None
if "vector_store" not in st.session_state:
    vs = MedicalVectorStore()
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        try:
            if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
                api_key = str(st.secrets["GOOGLE_API_KEY"]).strip()
        except Exception:
            pass
    if vs.get_document_count() == 0 and api_key:
        try:
            from src.loaders import MedicalDocumentLoader
            from src.splitter import MedicalTextSplitter
            from src.parser import MedicalDocumentParser
            raw_docs = MedicalDocumentLoader(config.KNOWLEDGE_BASE_DIR).load()
            if raw_docs:
                chunks = MedicalTextSplitter().split_documents(raw_docs)
                processed = MedicalDocumentParser().parse_sections(chunks)
                vs.add_documents(processed)
        except Exception as e:
            pass
    st.session_state["vector_store"] = vs
if "last_retrieved_docs" not in st.session_state:
    st.session_state["last_retrieved_docs"] = []
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(time.time())
if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = None
if "executed_tools" not in st.session_state:
    st.session_state["executed_tools"] = []
if "active_medicine_badge" not in st.session_state:
    st.session_state["active_medicine_badge"] = ""
if "sources_by_message_index" not in st.session_state:
    st.session_state["sources_by_message_index"] = {}

# Setup memory and router
memory = MedicalMemory()
router = IntentRouter()

# Apply Custom Pastel Lavender CSS Styles
apply_custom_css()

# Sidebar Layout
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #6A56BC; font-weight: 700; margin-bottom: 2px;'>ClinicRAG</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.85rem; color: #6E6685; font-weight: 500;'>Clinical Decision Support & Healthcare Assistant</p>", unsafe_allow_html=True)
    st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
    
    # 1. Patient Profile Memory Card with explicit Update button
    with st.expander("Patient Profile", expanded=False):
        profile = memory.get_patient_profile()
        
        input_age = st.text_input("Age:", value=profile.get("age", ""))
        input_gender = st.selectbox(
            "Gender:", 
            ["", "Male", "Female", "Other"], 
            index=["", "Male", "Female", "Other"].index(profile.get("gender", ""))
        )
        input_allergies = st.text_input("Allergies:", value=profile.get("allergies", ""))
        input_known_diseases = st.text_input("Known Chronic Diseases:", value=profile.get("known_diseases", ""))
        input_current_medicines = st.text_input("Current Medications:", value=profile.get("current_medicines", ""))
        
        if st.button("Update Profile", key="btn_update_profile", use_container_width=True):
            updated_profile = {
                "age": input_age,
                "gender": input_gender,
                "allergies": input_allergies,
                "known_diseases": input_known_diseases,
                "current_medicines": input_current_medicines
            }
            memory.update_patient_profile(updated_profile)
            st.success("Patient profile updated successfully.")
    
    # 2. Interactive Clinical Capabilities Grid Cards (Clean, no emojis)
    st.markdown("<h4 style='font-size: 0.90rem; font-weight: 600; color: #2E2842; margin-top: 0.5rem; margin-bottom: 8px;'>Clinical Capabilities</h4>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="capability-grid">
            <div class="capability-box">
                <div class="capability-title">Pharmacology</div>
                <div class="capability-desc">FDA DailyMed Labels & Drug Interactions</div>
            </div>
            <div class="capability-box">
                <div class="capability-title">Clinical Guidance</div>
                <div class="capability-desc">Symptoms, Diseases & Care Guidelines</div>
            </div>
            <div class="capability-box">
                <div class="capability-title">Emergency Care</div>
                <div class="capability-desc">First Aid & Acute Red-Flag Triage</div>
            </div>
            <div class="capability-box">
                <div class="capability-title">Health Metrics</div>
                <div class="capability-desc">BMI, BMR, TDEE, Water & Unit Converters</div>
            </div>
            <div class="capability-box">
                <div class="capability-title">Specialized Care</div>
                <div class="capability-desc">Pregnancy Milestones & Nutrition</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Expandable "How to Use" Guide (Clean, short, clear)
    with st.expander("How to Use ClinicRAG", expanded=False):
        st.markdown(
            """
            <div style="font-size: 0.84rem; color: #4E3F8A; line-height: 1.55;">
                <p><b>1. Symptoms & Guidelines:</b> Ask about symptoms, illnesses, or home care (e.g., <i>"What to do for viral fever?"</i>).</p>
                <p><b>2. Medications:</b> Check usage, warnings, and side effects (e.g., <i>"Paracetamol dosage and warnings"</i>).</p>
                <p><b>3. Drug Interactions:</b> Check if two medicines interact (e.g., <i>"Aspirin + Warfarin"</i>).</p>
                <p><b>4. Health Calculators:</b> Ask for BMI, BMR, TDEE, or water intake (e.g., <i>"Calculate my BMI for 65 kg and 5'4"</i>).</p>
                <p><b>5. Emergency First Aid:</b> Instant step-by-step guidance for CPR, burns, choking, or bleeding.</p>
                <p><b>6. Follow-up Questions:</b> Click any horizontal suggestion chip to ask next questions instantly.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Knowledge Base Status
    store = st.session_state["vector_store"]
    doc_count = store.get_document_count()
    
    if doc_count > 0:
        st.markdown(
            f"<div class='status-badge status-active'>Connected • {doc_count} Knowledge Base Chunks</div>", 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='status-badge status-inactive'>Indexed: Empty (0 Chunks)</div>", 
            unsafe_allow_html=True
        )
        if st.button("Sync & Index Knowledge Base", key="seed_kb_btn", use_container_width=True):
            with st.spinner("Indexing clinical guidelines into ChromaDB..."):
                from src.loaders import MedicalDocumentLoader
                from src.splitter import MedicalTextSplitter
                from src.parser import MedicalDocumentParser
                raw_docs = MedicalDocumentLoader(config.KNOWLEDGE_BASE_DIR).load()
                if raw_docs:
                    chunks = MedicalTextSplitter().split_documents(raw_docs)
                    processed = MedicalDocumentParser().parse_sections(chunks)
                    store.add_documents(processed)
                    st.rerun()
        
    st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)

    # 4. Session Controls
    st.markdown("<h4 style='font-size: 0.90rem; font-weight: 600; color: #2E2842; margin-bottom: 6px;'>Session Controls</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat", key="new_chat", use_container_width=True):
            memory.clear()
            st.session_state["last_retrieved_docs"] = []
            st.session_state["executed_tools"] = []
            st.session_state["active_medicine_badge"] = ""
            st.session_state["sources_by_message_index"] = {}
            st.rerun()
    with col2:
        if st.button("Reset All", key="reset_all", use_container_width=True):
            with st.spinner("Resetting..."):
                memory.clear_all()
                st.session_state["last_retrieved_docs"] = []
                st.session_state["executed_tools"] = []
                st.session_state["active_medicine_badge"] = ""
                st.session_state["sources_by_message_index"] = {}
                st.success("Session Fully Reset!")
                st.rerun()
                
    # 5. Export Conversation Option
    chat_messages = memory.get_messages()
    if chat_messages:
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        md_content = "# ClinicRAG - Clinical Conversation Export\n\n"
        prof = memory.get_patient_profile()
        md_content += f"**Age**: {prof.get('age') or 'N/A'} | **Gender**: {prof.get('gender') or 'N/A'} | **Allergies**: {prof.get('allergies') or 'None'}\n\n"
        md_content += "---\n\n"
        for m in chat_messages:
            role_label = "Patient" if m["role"] == "user" else "ClinicRAG Assistant"
            md_content += f"### {role_label}\n{m['content']}\n\n"
            
        st.download_button(
            label="Download Chat History (MD)",
            data=md_content,
            file_name="clinicrag_conversation.md",
            mime="text/markdown",
            use_container_width=True
        )

    # About Section
    st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
    st.caption("ClinicRAG is an AI clinical intelligence assistant. Sources: WHO Guidelines, FDA DailyMed Labels, and MedlinePlus Database.")
    st.caption(config.DISCLAIMER)

# Main Application Header (Sources on distinct next line, no emojis)
st.markdown(
    """
    <div style="margin-bottom: 0.75rem;">
        <h1 style="font-size: 2.2rem; font-weight: 700; color: #2E2842; margin-bottom: 2px; display: flex; align-items: center; gap: 12px;">
            ClinicRAG
            <span style="font-size: 0.8rem; font-weight: 600; background-color: #F3EFFA; color: #6A56BC; border: 1px solid #DED6ED; padding: 3px 10px; border-radius: 14px;">Clinical Decision Support</span>
        </h1>
        <div style="font-size: 0.90rem; color: #6E6685; margin-top: 4px;">
            <b>Sources:</b> WHO Guidelines, FDA DailyMed Labels, and MedlinePlus Database
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Visible Clinical Safety Disclaimer Banner
st.markdown(
    """
    <div class="clinical-disclaimer-banner">
        Notice: Clinical decision support only — not a substitute for professional medical advice.
    </div>
    """,
    unsafe_allow_html=True
)

# Check for API Key first before rendering chat
if not config.GOOGLE_API_KEY:
    st.info("Please set your GOOGLE_API_KEY in the sidebar or check your environment variables in .env to start chatting.")
    st.stop()

# Lazy load agent
if st.session_state["agent"] is None:
    try:
        st.session_state["agent"] = MedicalAgent()
    except Exception as e:
        st.error(f"Failed to initialize Agent: {exception_formatter(e)}")
        st.stop()

agent = st.session_state["agent"]

# Display chat messages history
messages = memory.get_messages()
for idx, msg in enumerate(messages):
    role = msg["role"]
    content = msg["content"]
    
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="🩺"):
            clean_text = content
            suggested_questions = []
            follow_up_pattern = r"(Suggested Follow-ups:|Suggested Follow-up Questions:|Follow-up Questions:)\s*\n1\.\s*(.*?)\n2\.\s*(.*?)\n3\.\s*(.*?)(?:\n|$)"
            match = re.search(follow_up_pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                clean_text = content[:match.start()].strip()
                suggested_questions = [match.group(2).strip(), match.group(3).strip(), match.group(4).strip()]
            
            st.markdown(clean_text)
            
            # Display visible retrieved sources evidence if recorded for this message
            evidence_list = st.session_state["sources_by_message_index"].get(idx, [])
            if evidence_list:
                st.markdown(
                    "<div class='retrieval-evidence-card'>"
                    "<div class='retrieval-header'>Retrieved Sources Evidence</div>"
                    + "".join([f"<div class='retrieval-item'>• {item['source']} — {item['section']} <span class='retrieval-relevance'>relevance: {item['score']:.0%}</span></div>" for item in evidence_list])
                    + "</div>",
                    unsafe_allow_html=True
                )

            # Display clickable follow-up questions only for the very latest assistant message arranged horizontally
            if idx == len(messages) - 1 and suggested_questions:
                st.markdown("<p style='font-size: 0.88rem; font-weight: 600; color: #4E3F8A; margin-top: 10px; margin-bottom: 6px;'>Suggested Follow-up Questions:</p>", unsafe_allow_html=True)
                followup_cols = st.columns(len(suggested_questions))
                for q_idx, q in enumerate(suggested_questions):
                    with followup_cols[q_idx]:
                        if st.button(q, key=f"hist_btn_{idx}_{q_idx}", use_container_width=True):
                            st.session_state["pending_prompt"] = q
                            st.rerun()

# Determine prompt to run (from chat input box OR clicked follow-up question)
user_input = st.chat_input("Ask symptoms, first aid guidelines, medicine details, or calculate health metrics...")
prompt_to_run = None

if st.session_state.get("pending_prompt"):
    prompt_to_run = st.session_state["pending_prompt"]
    st.session_state["pending_prompt"] = None
elif user_input:
    prompt_to_run = user_input

if prompt_to_run:
    # 1. Add User Message to Memory and render immediately on screen
    memory.add_message("user", prompt_to_run)
    with st.chat_message("user", avatar="👤"):
        st.write(prompt_to_run)
    
    # Reset tool metrics
    st.session_state["last_retrieved_docs"] = []
    st.session_state["executed_tools"] = []
    st.session_state["active_medicine_badge"] = ""
    
    # 2. Routing & Execution with sleek AI pulse animation loader
    profile_context = memory.get_patient_profile_string()
    history_str = memory.get_formatted_history_string()
    
    loader_placeholder = st.empty()
    loader_placeholder.markdown(
        """
        <div class="clinic-ai-loader">
            <div class="clinic-pulse-dot"></div>
            <div class="clinic-pulse-dot"></div>
            <div class="clinic-pulse-dot"></div>
            <span class="clinic-loader-text">ClinicRAG is thinking...</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    start_time = time.time()
    output_text = ""
    is_emergency = False
    
    try:
        routing_res = router.classify(prompt_to_run, history_str)
        is_emergency = routing_res["emergency_bypass"]
        
        if is_emergency:
            matched = routing_res.get("matched_flag", "Emergency")
            from src.tools import emergency_first_aid_guide
            first_aid_str = emergency_first_aid_guide.invoke(matched)
            
            output_text = (
                f"**CRITICAL EMERGENCY ALERT: Immediate medical attention required.**\n\n"
                f"**Danger signs detected: '{matched.upper()}'. Normal triage is suspended.**\n\n"
                f"{first_aid_str}\n\n"
                f"**Immediate Steps**:\n"
                f"1. **Call Emergency Hotline (911 / 112 / 102)** immediately.\n"
                f"2. Stay calm and sit down or lie down.\n"
                f"3. Unlock your door so first responders can enter.\n\n"
                f"**Do**:\n"
                f"- Loosen tight clothing.\n"
                f"- Rest quietly and monitor breathing.\n\n"
                f"**Don't**:\n"
                f"- Do NOT attempt to drive yourself to the emergency room.\n"
                f"- Do NOT ingest food, fluids, or unprescribed medications.\n\n"
                f"**Sources**:\n"
                f"- WHO Community Emergency Care Guidelines\n\n"
            )
        elif "Greeting" in routing_res.get("intents", []):
            output_text = (
                "Hello. I am ClinicRAG, your clinical decision support assistant. "
                "How can I assist you today with your symptoms, medications, or medical guidelines?\n\n"
                "Suggested Follow-ups:\n"
                "1. Common cold vs flu symptoms\n"
                "2. Check drug interactions\n"
                "3. Calculate Body Mass Index"
            )
        else:
            langchain_hist = memory.get_langchain_messages()
            response = agent.run(prompt_to_run, langchain_hist, profile_context)
            output_text = response.get("output", "I could not resolve your query.")
            
        duration = time.time() - start_time
        logger.info(f"Query executed in {duration:.4f}s. Intents classified: {routing_res.get('intents')}")
        
    except Exception as e:
        output_text = f"An unexpected error occurred while routing your query: {exception_formatter(e)}"
        logger.error(f"UI chat error: {e}")
    finally:
        loader_placeholder.empty()
            
    # 4. Save Assistant Output to Memory
    memory.add_message("assistant", output_text)
    
    # 5. Save Retrieval Evidence for this message index
    assistant_msg_idx = len(memory.get_messages()) - 1
    retrieved_docs = st.session_state.get("last_retrieved_docs", [])
    if retrieved_docs and not is_emergency:
        evidence_items = []
        for doc in retrieved_docs[:4]:
            meta = doc.metadata
            src = meta.get("source_name", "Medical Reference")
            sec = meta.get("section") or meta.get("category") or "Overview"
            conf = meta.get("confidence_score", 0.88)
            evidence_items.append({
                "source": src,
                "section": sec,
                "score": conf
            })
        st.session_state["sources_by_message_index"][assistant_msg_idx] = evidence_items
        
    st.rerun()
