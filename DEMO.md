🏁 AI Race Engineer — Demo Guide

This document explains how to run the AI Race Engineer system locally after cloning the repository.

The system includes:

FastAPI backend

Monte Carlo strategy engine

RAG knowledge layer

Tool-calling LLM agent

Streamlit dashboard UI

🔧 System Requirements

Python 3.10+

pip

Internet connection (for OpenAI API + FastF1 download)

1️⃣ Clone the Repository
git clone https://github.com/YOUR_USERNAME/ai-race-engineer.git
cd ai-race-engineer

2️⃣ Create a Virtual Environment
Mac / Linux
python -m venv venv
source venv/bin/activate

Windows
python -m venv venv
venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Configure OpenAI API Key

Create a file named:

.env


in the project root directory.

Add your API key:

OPENAI_API_KEY=your-api-key-here


⚠️ Important:

Do not add quotes

Do not commit this file to GitHub

5️⃣ Generate Required Race Data

Before starting the system, generate telemetry data and computed features.

Run the following commands in order:

python ingestion/load_session.py
python ingestion/detect_stints.py
python ingestion/compute_features.py


This will generate:

data/laps.parquet

data/stints.parquet

data/stint_features.parquet

These files are required for the API to function.

6️⃣ Start the Backend API
python -m uvicorn api.main:app --reload


If successful, you will see:

Uvicorn running on http://127.0.0.1:8000


You can verify the API by visiting:

http://127.0.0.1:8000/docs


This opens interactive Swagger documentation.

7️⃣ Launch the Streamlit Dashboard

Open a new terminal window (keep the API running) and execute:

streamlit run dashboard.py


The dashboard will open automatically in your browser.

🧠 How to Use the Demo

Inside the dashboard:

Select a driver

Adjust pit loss

Adjust safety car probability

Run the strategy simulation

Ask the AI race engineer questions such as:

“What happens if pit loss drops to 12 seconds?”

“Explain undercut strategy.”

“Is 2-stop better under safety car conditions?”

“What does FIA require regarding tyre compounds?”

The system combines:

Monte Carlo simulation

Strategy optimization logic

Retrieval-Augmented Generation (RAG)

Tool-calling LLM reasoning

🏗 System Architecture
Streamlit Dashboard
        ↓
FastAPI Backend
        ↓
Monte Carlo Strategy Engine
        ↓
RAG Knowledge Retrieval (Chroma)
        ↓
LLM Tool-Calling Agent

🛠 Troubleshooting
ModuleNotFoundError

Ensure your virtual environment is activated before running commands.

Missing Data Files

Re-run the ingestion scripts listed in Step 5.

OpenAI Authentication Error

Verify that your .env file contains a valid API key.

🚀 What This Project Demonstrates

Race strategy simulation

Probabilistic Monte Carlo modeling

Tool-calling LLM orchestration

Retrieval-Augmented Generation (RAG)

API-based architecture (FastAPI)

Frontend integration (Streamlit)