# Setup and Installation

Follow these steps to set up **ClinicRAG** in your local development environment.

## Prerequisites
- Python 3.11 or higher
- A Google AI Studio API key (Gemini API key)

## Step 1: Clone Repository
```bash
git clone https://github.com/Kritvi0208/ClinicRAG.git
cd ClinicRAG
```

## Step 2: Virtual Environment Setup
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

## Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 4: Environment Variables
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
LOG_LEVEL=INFO
```

## Step 5: Build Vector Store
Parse documents under `data/knowledge_base/` and build the ChromaDB index:
```bash
python scripts/build_vector_store.py
```

## Step 6: Launch Web App
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.
