# 🏁 AI Race Engineer — Demo Guide

Step-by-step instructions to run the system locally.

---

## System Requirements

- Python 3.10+
- pip
- Internet connection (for OpenAI API + FastF1 data download)

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-race-engineer.git
cd ai-race-engineer
```

### 2. Create Virtual Environment

```bash
# Mac / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure OpenAI API Key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your-api-key-here
```

Do not add quotes. Do not commit this file to GitHub.

### 5. Generate Race Data

Run the ingestion pipeline in order:

```bash
python ingestion/load_session.py
python ingestion/detect_stints.py
python ingestion/compute_features.py
```

This generates `data/laps.parquet`, `data/stints.parquet`, and `data/stint_features.parquet`.

### 6. Start the Backend API

```bash
python -m uvicorn api.main:app --reload
```

Verify at: http://127.0.0.1:8000/docs (Swagger UI)

### 7. Launch the Dashboard

In a new terminal (keep the API running):

```bash
streamlit run dashboard.py
```

---

## Using the Demo

Inside the dashboard:

1. **Select a driver** from the dropdown
2. **Adjust parameters**: pit loss, safety car probability, Monte Carlo iterations
3. **Run the simulation** — view strategy recommendation, win rates, and visualizations
4. **Ask the AI race engineer** questions:
   - "What happens if pit loss drops to 12 seconds?"
   - "Explain undercut strategy."
   - "Is 2-stop better under safety car conditions?"
   - "What does FIA require regarding tyre compounds?"

The AI agent calls the simulation engine for numerical questions and retrieves FIA rules/strategy theory for knowledge questions.

---

## Architecture

```
Streamlit Dashboard
        ↓
FastAPI Backend (/recommend, /chat)
        ↓
Monte Carlo Strategy Engine (vectorized NumPy)
        ↓
RAG Knowledge Retrieval (ChromaDB)
        ↓
LLM Tool-Calling Agent (GPT-4o-mini)
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Activate virtual environment first |
| Missing data files | Re-run ingestion scripts (Step 5) |
| OpenAI authentication error | Check `.env` file has valid API key |
| Cannot connect to API | Ensure backend is running (Step 6) |
