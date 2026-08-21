# Retrieval-Augmented Generation (RAG)

ClinicRAG uses a hybrid Retrieval-Augmented Generation pipeline over an indexed medical knowledge base and official pharmaceutical records.

## Document Lifecycle
```
[WHO Guidelines & MedlinePlus Markdown]
       │
       ▼ (src/loaders.py)
[Document Objects + Metadata]
       │
       ▼ (src/splitter.py)
[Recursive Text Chunks - Size 1000, Overlap 200]
       │
       ▼ (src/embeddings.py)
[Vector Embeddings - Google Gemini]
       │
       ▼ (src/vector_store.py)
[Persistent ChromaDB Store]
```

## Retrieval Strategy
- **Maximal Marginal Relevance (MMR)**: Balances similarity with diversity to avoid redundant chunks.
- **Confidence Calibration**: Calculates distance-based relevance percentage scores.
- **Direct FDA DailyMed Label Bypass**: Queries on-demand HL7 v3 XML parser for exact drug labels.
- **Verifiable Source Attribution**: Retains source document title, category, section, and relevance score for demonstrable clinical RAG.
