# Architecture Overview

This page describes the technical architecture of **ClinicRAG**.

## Component Layout

```
User Prompt
 │
 ├──> Streamlit UI (app.py)
       │
       ├──> Intent & Safety Router (src/router.py)
       │     ├──> Emergency Red-Flag Bypass (Immediate Tier 1 Response)
       │     └──> Fast Greeting Interception
       │
       ├──> Patient Profile Memory (src/memory.py)
       │
       └──> LangChain Tool Calling Agent (src/agent.py)
             │
             ├──> Multi-Model LLM Cascade (Gemini 3.7 / 3.6 / 3.5 Flash)
             │
             ├──> 16 Clinical Tools (src/tools.py)
             │     ├──> FDA DailyMed SPL XML Parser (src/fda_parser.py)
             │     ├──> Drug Interaction Matrix Lookup
             │     ├──> Health Metric Calculators (BMI, BMR, TDEE, Water)
             │     └──> Emergency First Aid Protocols
             │
             └──> Hybrid Retriever (src/retriever.py)
                   │
                   └──> ChromaDB (src/vector_store.py)
                         └──> Vector Database (data/knowledge_base/ -> chroma_db/)
```

## System Modules
- **`src/config.py`**: Centralized configuration for model endpoints, fallback chains, thresholds, and paths.
- **`src/logger.py`**: Rotating file logger (`clinicrag.log`) tracking tool executions, retrieval latency, and tokens.
- **`src/router.py`**: Deterministic keyword triage + LLM structured classification.
- **`src/retriever.py`**: Custom vector retriever with Maximal Marginal Relevance (MMR) and L2 distance confidence calibration.
- **`src/fda_parser.py`**: On-demand XML parser for 3,330+ FDA DailyMed SPL medication labels.
- **`src/agent.py`**: Agent executor with multi-tier model cascade and local deterministic fallback.
