# GiftGenie Backend (FastAPI + Gemini Agents)

This repository contains the backend for **GiftGenie**, a small AI-powered gift recommendation tool built as part of the **Kaggle x Google 5-Day AI Agents Intensive Capstone Project**.

The goal of this backend is to show how a small but real multi-agent system can take simple user details and produce thoughtful, structured gift suggestions.

The frontend (Next.js) is in a separate repo and sends requests to this backend.

---

# 1. Project Purpose

The idea behind GiftGenie is simple:  
Most people struggle to think of a good gift when a birthday, anniversary, or event comes up. Search results are generic, and manually browsing ideas takes too much time.

GiftGenie automates this by turning a few details about the recipient into **personalized gift ideas**, using a lightweight agent workflow powered by Gemini.

This project was submitted under the **Concierge Agents** track.

---

# 2. How the Agent System Works

The backend uses a small multi-agent pattern. Each step is simple on purpose, but together they form a clear agent workflow:

## **Step 1 — Input Structuring Agent**
Cleans the raw fields and builds a consistent “persona” object for Gemini to work with.

## **Step 2 — Gift Generation Agent (LLM-powered)**
Calls **Gemini** to generate 5 JSON-formatted gift ideas:
- title  
- reason  
- approximate price range  

This ensures deterministic structure for the frontend.

## **Step 3 — Filtering Tool**
A small custom tool (Python function) checks:
- duplicates  
- similarity to previously-suggested gifts  
- approximate budget alignment  

This tool behaves like a post-processing agent step.

## **Step 4 — Basic Memory**
A simple JSON file (`memory.json`) stores recent requests.  
This shows the concept of long-term memory without over-engineering.

## **Step 5 — Logging**
A log file (`logs/agent.log`) tracks generation steps to demonstrate observability.

This setup covers the core Kaggle requirements:
- **Multi-agent flow**
- **LLM-powered agent**
- **Custom tool**
- **Basic memory**
- **Simple logging (observability)**
- **Evaluation script**

---

# 3. Repository Structure

```
.
├── api.py           # FastAPI app + /giftgenie endpoint
├── main.py          # Agent workflow, prompts, and filtering tool
├── evaluate.py      # Small script to test gift quality
├── memory.json      # Long-term memory dump (basic)
├── logs/
│   └── agent.log    # Logging for observability
├── requirements.txt
└── README.md
```

---

# 4. Running Locally

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Set your Gemini API key:

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY = "YOUR_KEY"
```

**macOS / Linux:**
```bash
export GEMINI_API_KEY="YOUR_KEY"
```

### Start the server:
```bash
uvicorn api:app --reload --port 8000
```

### API URLs:
- Swagger docs → http://localhost:8000/docs  
- Main endpoint → POST http://localhost:8000/giftgenie  

### Example request:
```json
{
  "recipient_name": "Sam",
  "age": "27",
  "relationship": "friend",
  "occasion": "birthday",
  "interests": "art, music",
  "dislikes": "noisy gadgets",
  "budget": "50"
}
```

---

# 5. Evaluation Script

The project includes a simple test harness:

```bash
python evaluate.py
```

It runs the agent on a handful of predefined cases and prints:
- a preview of generated gifts  
- interest matching  
- duplicate detection  
- budget sanity check  

---

# 6. Deployment (Cloud Run)

The backend is deployed to **Google Cloud Run**.

Cloud Run provides:
- automatic HTTPS  
- environment variable support  
- autoscaling  
- easy integration with GitHub  


### Actual API endpoint:
```
https://kaggle-capstone-giftgenie-1056868419677.europe-west1.run.app
```

### Environment variable configured:
```
GEMINI_API_KEY
```

The frontend uses this URL via `GIFTGENIE_BACKEND_URL`.

---

# 7. Technologies Used

- Python 3  
- FastAPI  
- Gemini  
- Multi-agent pattern  
- Custom tool for filtering  
- Basic memory store  
- Logging for observability  
- Cloud Run deployment  

---

# 8. Frontend Repository

The GiftGenie UI is built separately:

```
https://github.com/Praneeth00/giftgenie-web
```

Live website (frontend + backend wired together):

```
https://giftgenie-web.vercel.app/
```

The frontend speaks only to this backend and handles all display logic.

---

# 9. Notes for Reproducibility (Kaggle Requirement)

Anyone with a Gemini API key can run this project locally by:

1. Cloning the repo  
2. Installing dependencies  
3. Adding `GEMINI_API_KEY`  
4. Running `uvicorn api:app --reload`  

No other setup is required.

---

# 10. License

This project was created solely for educational use as part of the Kaggle x Google AI Agents Intensive.

