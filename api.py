from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import (
    setup_logging,
    setup_gemini,
    run_pipeline,
    load_memory,
    summarize_memory,
    append_memory_entry,
)


app = FastAPI(title="GiftGenie Backend (JSON Pipeline)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None


class GiftRequest(BaseModel):
    recipient_name: str
    age: Optional[str] = None
    relationship: Optional[str] = None
    occasion: Optional[str] = None
    budget: Optional[str] = None
    interests: Optional[str] = None
    dislikes: Optional[str] = None
    save_choice: bool = False
    chosen_gift: Optional[str] = None


class Gift(BaseModel):
    title: str
    reason: str
    priceRange: Optional[str] = ""


class GiftResponse(BaseModel):
    persona_profile: Dict[str, Any]
    gifts: List[Gift]
    memory_summary: List[Dict[str, Any]]


@app.on_event("startup")
def startup_event():
    """
    Initialize logging and Gemini model once on server start.
    """
    global model
    setup_logging()
    model = setup_gemini()


@app.post("/giftgenie", response_model=GiftResponse)
def giftgenie_endpoint(req: GiftRequest):
    """
    HTTP endpoint for the GiftGenie pipeline.

    This is what your Next.js app will call:
    - Uses the same multi-agent pipeline as CLI and evaluation.
    - Returns:
        * persona_profile
        * gifts (final_gifts – list of {title, reason, priceRange})
        * memory_summary (last few saved choices)
    """
    raw_info = {
        "recipient_name": req.recipient_name or "the recipient",
        "age": req.age or "unknown",
        "relationship": req.relationship or "friend",
        "occasion": req.occasion or "special occasion",
        "budget": req.budget or "flexible",
        "interests": req.interests or "general interests",
        "dislikes": req.dislikes or "none specified",
    }

    pipeline_result = run_pipeline(model, raw_info)
    persona_profile = pipeline_result["persona_profile"]
    final_gifts = pipeline_result["final_gifts"]

    if req.save_choice and req.chosen_gift:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "persona_profile": persona_profile,
            "chosen_gift": req.chosen_gift,
            "notes": "Saved from API call (frontend integration)",
        }
        append_memory_entry(entry)

    full_memory = load_memory()
    memory_summary = summarize_memory(full_memory, limit=3)

    return GiftResponse(
        persona_profile=persona_profile,
        gifts=[Gift(**g) for g in final_gifts],
        memory_summary=memory_summary,
    )
