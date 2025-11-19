🧞‍♂️ GiftGenie – Multi-Agent Gift Concierge
Kaggle x Google – AI Agents Intensive (Concierge Agents Track)

GiftGenie is an AI-powered personal gift concierge that uses a multi-agent system, a custom Gemini tool, long-term memory, evaluation, and a clean Next.js UI to deliver exactly 5 personalized, budget-aware, meaningful gift ideas for any recipient.

This repository contains the backend, which powers all agent reasoning and is the official Kaggle Capstone submission.

Frontend repo (UI):
➡️ https://github.com/Praneeth00/giftgenie-web

⭐ 1. Problem & Motivation

Choosing the perfect gift is mentally exhausting:

You don’t know if the gift will be appreciated

Budgets vary

Every person has a unique personality

Online “top 10 gifts” lists feel generic

GiftGenie solves this by acting as a personal AI gift concierge, powered by agents + Gemini.

⭐ 2. Multi-Agent Architecture (Core of Project)

GiftGenie uses three core agents + one tool:

🟣 1. Persona Agent

Transforms raw user inputs into structured persona profile:

age

relationship

interests

dislikes

budget

occasion

🔵 2. Gift Ideas Agent (Gemini 2.0 Flash)

Generates EXACT 5 gifts in strict JSON:

{
  "gifts": [
    { "title": "...", "reason": "...", "priceRange": "..." }
  ]
}

🟠 3. Filter Agent

Uses a custom tool to refine gifts based on budget.

🟡 4. Tool: price_filter_tool (custom)

Gemini-powered JSON → JSON tool that:

Removes over-budget gifts

Reorders list

Adds budget awareness

Returns exactly 5 refined items

🟢 5. Orchestrator

Connects all agents, memory, evaluation, and API.

⭐ 3. System Architecture Diagram
                                   ┌──────────────────────────┐
                                   │   Next.js Frontend (UI)  │
                                   └─────────┬────────────────┘
                                             │ (POST /api/suggest-gifts)
                                             ▼
                             ┌────────────────────────────────────────┐
                             │         FastAPI Backend (This Repo)    │
                             └───────────┬────────────────────────────┘
                                         │
             ┌───────────────────────────┼──────────────────────────────┬──────────────────────────┐
             ▼                           ▼                              ▼                          ▼
     ┌────────────────┐          ┌─────────────────┐          ┌─────────────────┐         ┌────────────────┐
     │ Persona Agent  │   →      │ Gift Ideas Agent│   →      │ Filter Agent    │   →     │ Final JSON     │
     └────────────────┘          └─────────────────┘          │ + price tool    │         │ (5 items)      │
                                                               └─────────────────┘         └────────────────┘


⭐ 4. Features Satisfying Kaggle Capstone Requirements
✔ Multi-agent system
✔ Custom tool (JSON→JSON LLM agent tool)
✔ Gemini API usage
✔ Sessions & state
✔ Long-term memory (memory.json)
✔ Context engineering
✔ Observability (logs/agent.log)
✔ Agent evaluation (evaluate.py)
✔ Deployment-ready backend (FastAPI)
✔ JSON-based interface for UI integration

Everything required by the rubric is implemented clearly.

⭐ 5. Repository Structure
backend/
  main.py               <-- Multi-agent pipeline
  api.py                <-- FastAPI backend (official endpoint)
  evaluate.py           <-- Agent evaluation
  memory.json           <-- Long-term memory store
  logs/agent.log        <-- Observability logs
  requirements.txt
  README.md             <-- This file


Frontend UI repo (Next.js):
➡️ https://github.com/Praneeth00/giftgenie-web

⭐ 6. Setup Instructions (Backend)
1. Install dependencies
pip install -r requirements.txt

2. Set Gemini API key
Windows PowerShell:
$env:GEMINI_API_KEY="YOUR_KEY"

Mac/Linux:
export GEMINI_API_KEY="YOUR_KEY"

3. Run FastAPI backend
uvicorn api:app --reload --port 8000


Backend endpoint:

POST http://localhost:8000/giftgenie

⭐ 7. Running Evaluation (Agent Evaluation)
python evaluate.py


This prints:

Persona preview

Final 5 gift ideas

Interest coverage score

Budget alignment score

Logs in:

logs/agent.log

⭐ 8. Deployment (Optional, +5 Bonus)

Backend is Cloud Run–ready:

gcloud run deploy giftgenie-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated


Then set:

GIFTGENIE_BACKEND_URL="https://your-cloudrun-url/giftgenie"

⭐ 9. Technologies Used

Gemini 2.0 Flash

Python 3.10+

FastAPI

Multi-agent architecture

Custom tools

JSON LLM outputs

Observability & logging

Evaluation metrics

⭐ 10. License

MIT License.