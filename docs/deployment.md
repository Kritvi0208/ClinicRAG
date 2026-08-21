# Deployment Guidelines

Follow these practices to deploy **ClinicRAG** into local, staging, or production environments.

## Local Deployment
You can run ClinicRAG locally by executing Streamlit:
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Cloud Deployment (Streamlit Cloud / Render / Hugging Face Spaces)
1. **Repository Setup**: Push the complete codebase to GitHub.
2. **Environment Secrets**: Add `GOOGLE_API_KEY` to your cloud hosting environment variables.
3. **Database Build**: Run `python scripts/build_vector_store.py` during deployment or allow on-demand indexing.
4. **Performance**: Optimized with client caching, lazy loading, and multi-model fallback to run smoothly within standard cloud container limits.
