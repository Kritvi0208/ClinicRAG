# ClinicRAG

Welcome to the documentation for **ClinicRAG**, an advanced clinical decision support and medical intelligence system.

## Overview
ClinicRAG is a Retrieval-Augmented Generation (RAG) assistant designed for clinical decision support, health education, pharmaceutical exploration, and emergency red-flag triage.

- **Streamlit**: Modern pastel-themed healthcare interface.
- **LangChain**: Tool-calling agent execution, prompt orchestration, and sliding memory.
- **ChromaDB**: Persistent vector database for WHO and MedlinePlus medical literature.
- **FDA DailyMed HL7 v3 XML**: Structured Product Labeling parser across 3,330+ indexed drugs.
- **Google Gemini 3.7 Flash & Fallback Cascade**: High-speed reasoning with multi-model resilience.

## Key Features
- **Authoritative RAG Retrieval**: Verified clinical guidelines from WHO, NIH, and MedlinePlus.
- **Structured Output**: Rigorous clinical formatting with emergency indicators, actionable steps, and verifiable sources.
- **16 Clinical Tools**:
  - Pharmacology: FDA Drug Labels, Drug Interactions, and Dosage Guidelines.
  - Clinical Guidance: Symptom Checker, Disease Overview, Nutrition, Pregnancy Milestones.
  - Emergency Care: Red-Flag Triage and Step-by-Step First Aid.
  - Health Metrics: BMI, BMR, Calorie Requirements, Water Intake, and Unit Converters.
- **Patient Profile Memory**: Dynamically injected patient state (age, gender, chronic conditions, allergies, active medications).
- **Verifiable Evidence & Source Attribution**: Full document name, section, and relevance score tracking for demonstrable RAG.
