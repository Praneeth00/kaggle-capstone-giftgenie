import os
import json
import textwrap
import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from google import generativeai as genai
except ImportError:
    genai = None


MEMORY_FILE = "memory.json"

def setup_logging():
    """
    Configure logging to write both to console and to logs/agent.log.
    """
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/agent.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.info("✅ Logging initialized. Writing to logs/agent.log")

def load_memory() -> List[Dict[str, Any]]:
    """
    Load long-term memory from a JSON file acting as a simple 'Memory Bank'.
    """
    if not os.path.exists(MEMORY_FILE):
        logging.info("No memory file found yet, starting fresh.")
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            logging.info("Loaded %d memory entries from %s", len(data), MEMORY_FILE)
            return data
        logging.warning("Memory file format invalid, resetting.")
        return []
    except Exception as e:
        logging.error("Error loading memory file: %s", e)
        return []


def save_memory(memory_list: List[Dict[str, Any]]) -> None:
    """
    Save the full memory list to disk.
    """
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_list, f, indent=2, ensure_ascii=False)
        logging.info("Saved %d memory entries to %s", len(memory_list), MEMORY_FILE)
    except Exception as e:
        logging.error("Error saving memory file: %s", e)


def append_memory_entry(entry: Dict[str, Any]) -> None:
    """
    Append a single memory entry and persist to disk.
    """
    memory = load_memory()
    memory.append(entry)
    save_memory(memory)
    logging.info(
        "Appended new memory entry for %s (%s).",
        entry.get("persona_profile", {}).get("display_name", "unknown"),
        entry.get("persona_profile", {}).get("occasion", "unknown"),
    )


def print_memory_summary(memory: List[Dict[str, Any]]) -> None:
    """
    Print a short summary of past sessions for the CLI user.
    """
    if not memory:
        print("🧠 No previous GiftGenie sessions found yet.\n")
        return

    print(f"🧠 Loaded {len(memory)} past GiftGenie session(s). Here are the latest:\n")
    for item in memory[-3:]:
        when = item.get("timestamp", "unknown time")
        persona = item.get("persona_profile", {})
        gift = item.get("chosen_gift", "N/A")
        name = persona.get("display_name", "someone")
        occasion = persona.get("occasion", "some occasion")
        print(f"- [{when}] Gift for {name} ({occasion}): {gift}")
    print()


def summarize_memory(memory: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Return the last few memory entries in a machine-readable form.
    """
    if not memory:
        return []
    return memory[-limit:]

def setup_gemini():
    """
    Configure the Gemini client using an environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set.\n"
            "Set it before running this script."
        )

    if genai is None:
        raise RuntimeError(
            "google-generativeai package not installed.\n"
            "Install it with:  pip install google-generativeai"
        )

    genai.configure(api_key=api_key)
    model_name = "gemini-2.0-flash-exp"  # adjust if needed
    model = genai.GenerativeModel(model_name)

    logging.info("Gemini configured with model: %s", model_name)
    return model

def collect_user_inputs() -> Dict[str, str]:
    """
    Ask the user basic questions about the gift (CLI only).
    For API usage, pass a raw_info dict directly to run_pipeline().
    """
    print("🧞‍♂️ Welcome to GiftGenie – multi-agent gift concierge\n")

    recipient_name = input("Who is this gift for? (e.g., my sister, my manager): ").strip()
    age = input("Approximate age? (e.g., 10, 25, 40s): ").strip()
    relationship = input("Relationship? (e.g., friend, cousin, coworker): ").strip()
    occasion = input("What is the occasion? (e.g., birthday, promotion, thank you): ").strip()
    budget = input("What is your budget? (e.g., 25, 50, 50-75): ").strip()
    interests = input("What do they like? (e.g., books, games, travel, plants): ").strip()
    dislikes = input("Anything to avoid? (e.g., alcohol, tech, perfumes) [optional]: ").strip()

    info = {
        "recipient_name": recipient_name or "the recipient",
        "age": age or "unknown",
        "relationship": relationship or "friend",
        "occasion": occasion or "special occasion",
        "budget": budget or "flexible",
        "interests": interests or "general interests",
        "dislikes": dislikes or "none specified",
    }

    logging.info(
        "Collected user inputs: recipient=%s, age=%s, relationship=%s, occasion=%s, budget=%s",
        info["recipient_name"],
        info["age"],
        info["relationship"],
        info["occasion"],
        info["budget"],
    )
    return info

def persona_agent(raw_info: Dict[str, str]) -> Dict[str, Any]:
    """
    Persona agent:
    Turn raw user input into a clean persona profile (structured state).
    """
    profile = {
        "display_name": raw_info["recipient_name"],
        "age": raw_info["age"],
        "relationship": raw_info["relationship"],
        "occasion": raw_info["occasion"],
        "budget": raw_info["budget"],
        "interests": [s.strip() for s in raw_info["interests"].split(",") if s.strip()],
        "dislikes": [s.strip() for s in raw_info["dislikes"].split(",") if s.strip()],
    }

    print("\n🧩 Persona Agent Output (structured profile):")
    print(profile)
    print()

    logging.info(
        "Persona agent built profile for %s (occasion=%s, budget=%s)",
        profile["display_name"],
        profile["occasion"],
        profile["budget"],
    )

    return profile

def _safe_load_json(text: str) -> Any:
    """
    Try to load JSON from a model response robustly.
    - Strip code fences
    - Extract substring from first '{' to last '}'
    """
    if not text:
        raise ValueError("Empty model response")

    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "json" in text[:10].lower():
            text = text[text.lower().find("json") + 4 :].strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        return json.loads(candidate)

    raise ValueError("Could not parse JSON from model text")

def build_gift_prompt(persona: Dict[str, Any]) -> str:
    """
    Turn the persona dict into a prompt for the gift ideas agent.
    This version requires STRICT JSON output.
    """
    interests_str = ", ".join(persona["interests"]) if persona["interests"] else "general interests"
    dislikes_str = ", ".join(persona["dislikes"]) if persona["dislikes"] else "none specified"

    prompt = f"""
    You are an expert gift concierge.

    TASK:
    Propose EXACTLY 5 thoughtful gift ideas for the recipient below.
    Return STRICT JSON ONLY in this exact shape – no extra text, no markdown:

    {{
      "gifts": [
        {{
          "title": "Short gift name",
          "reason": "1–3 sentence explanation why this fits the persona",
          "priceRange": "Approximate price range like $20–$40 or 1500–2500 INR"
        }}
      ]
    }}

    Recipient persona:
    - Display name: {persona['display_name']}
    - Age: {persona['age']}
    - Relationship to the user: {persona['relationship']}
    - Occasion: {persona['occasion']}
    - Budget: {persona['budget']} (in USD or equivalent)
    - Interests: {interests_str}
    - Things to avoid: {dislikes_str}

    Requirements:
    - "gifts" MUST be an array with exactly 5 objects.
    - Every object MUST have string fields: "title", "reason", "priceRange".
    - Do not include any keys other than "gifts", "title", "reason", "priceRange".
    - Do not include markdown, code fences, or commentary – ONLY the JSON object.
    """

    return textwrap.dedent(prompt).strip()


def gift_ideas_agent(model, persona: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    LLM-powered agent that calls Gemini to generate initial gift ideas as strict JSON.
    Returns a Python list of gift dicts:
      [{"title": "...", "reason": "...", "priceRange": "..."}, ...]
    """
    logging.info("Gift ideas agent: generating ideas for %s", persona["display_name"])
    prompt = build_gift_prompt(persona)

    print("✨ Gift Ideas Agent: Asking Gemini for gift suggestions (JSON)...\n")
    response = model.generate_content(prompt)

    text = getattr(response, "text", None) or str(response)
    data = _safe_load_json(text)

    gifts = data.get("gifts", [])
    if not isinstance(gifts, list):
        raise ValueError("Model returned JSON without 'gifts' array")

    normalized: List[Dict[str, str]] = []
    for g in gifts:
        if not isinstance(g, dict):
            continue
        normalized.append(
            {
                "title": str(g.get("title", "Gift idea")).strip(),
                "reason": str(g.get("reason", "")).strip(),
                "priceRange": str(g.get("priceRange", "")).strip(),
            }
        )

    logging.info(
        "Gift ideas agent: received %d gifts for %s",
        len(normalized),
        persona["display_name"],
    )
    return normalized

def price_filter_tool(model, gifts: List[Dict[str, str]], budget: str) -> List[Dict[str, str]]:
    """
    A 'tool' that uses Gemini to re-check the ideas against the budget
    and return a filtered / re-ranked list as STRICT JSON.

    Input: list of gift objects
    Output: list of gift objects (same shape)
    """
    tool_prompt = f"""
    You are a gift budget filter tool.

    The user has the following budget: {budget} (in USD or equivalent).

    Here is a JSON array of candidate gift ideas:

    {json.dumps(gifts, indent=2, ensure_ascii=False)}

    TASK:
    - Re-check these ideas against the budget.
    - If some gifts clearly exceed the budget, either remove them
      or keep them but mark them as "stretch options" in the reason.
    - Return EXACTLY 5 ideas again, ordered from BEST budget fit to least fit.
    - Each idea must remain an object with ONLY:
        - "title"
        - "reason" (update if needed to mention budget fit)
        - "priceRange"
    - Return STRICT JSON ONLY of the form:

      {{
        "gifts": [
          {{
            "title": "...",
            "reason": "...",
            "priceRange": "..."
          }}
        ]
      }}

    - Do NOT include markdown, comments, or any text outside the JSON.
    """

    tool_prompt = textwrap.dedent(tool_prompt).strip()

    logging.info("Price filter tool: applying budget=%s", budget)
    print("🧮 Price Filter Tool: Refining ideas based on budget (JSON)...\n")
    response = model.generate_content(tool_prompt)

    text = getattr(response, "text", None) or str(response)
    data = _safe_load_json(text)

    new_gifts = data.get("gifts", [])
    if not isinstance(new_gifts, list):
        raise ValueError("Price filter tool returned JSON without 'gifts' array")

    normalized: List[Dict[str, str]] = []
    for g in new_gifts:
        if not isinstance(g, dict):
            continue
        normalized.append(
            {
                "title": str(g.get("title", "Gift idea")).strip(),
                "reason": str(g.get("reason", "")).strip(),
                "priceRange": str(g.get("priceRange", "")).strip(),
            }
        )

    logging.info("Price filter tool: completed budget filtering (%d gifts).", len(normalized))
    return normalized

def filter_agent(model, persona: Dict[str, Any], gifts: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter agent that delegates budget checking to price_filter_tool.
    """
    budget = persona.get("budget", "flexible")
    logging.info("Filter agent: starting with budget=%s", budget)
    print(f"🔍 Filter Agent: Applying budget filter for budget = {budget}\n")

    filtered_gifts = price_filter_tool(model, gifts, budget)

    logging.info("Filter agent: finished filtering for %s", persona["display_name"])
    return filtered_gifts

def run_pipeline(model, raw_info: Dict[str, str]) -> Dict[str, Any]:
    """
    Core multi-agent pipeline:

      1. Persona agent -> structured profile.
      2. Gift ideas agent -> initial gifts (JSON list).
      3. Filter agent -> budget-aware refinement (JSON list).

    Returns a dict with:
      - persona_profile
      - initial_gifts (list[Gift])
      - final_gifts (list[Gift])

    This is used by:
      - CLI
      - FastAPI backend
      - Evaluation harness
    """
    logging.info("Pipeline: starting for recipient=%s", raw_info.get("recipient_name", "unknown"))

    persona_profile = persona_agent(raw_info)
    initial_gifts = gift_ideas_agent(model, persona_profile)
    final_gifts = filter_agent(model, persona_profile, initial_gifts)

    result = {
        "persona_profile": persona_profile,
        "initial_gifts": initial_gifts,
        "final_gifts": final_gifts,
    }

    logging.info(
        "Pipeline: completed for %s (occasion=%s, budget=%s)",
        persona_profile["display_name"],
        persona_profile["occasion"],
        persona_profile["budget"],
    )
    return result

def orchestrator_agent(model, session_state: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    High-level controller for CLI sessions:
      1. Collects user inputs from stdin.
      2. Calls run_pipeline(...) to execute the multi-agent workflow.
      3. Stores key info in session_state.
    """
    logging.info("Orchestrator: starting new CLI session pipeline.")
    raw_info = collect_user_inputs()

    pipeline_result = run_pipeline(model, raw_info)

    session_state["persona_profile"] = pipeline_result["persona_profile"]
    session_state["initial_gifts"] = pipeline_result["initial_gifts"]
    session_state["final_gifts"] = pipeline_result["final_gifts"]

    logging.info(
        "Orchestrator: CLI session pipeline completed for %s",
        pipeline_result["persona_profile"]["display_name"],
    )
    return pipeline_result["final_gifts"]

def main():
    """
    CLI entry point for GiftGenie.

    Demonstrates:
    - Multi-agent workflow (persona, ideas, filter)
    - Custom tool (price_filter_tool) using LLM
    - Sessions & state (session_state)
    - Long-term memory (memory.json)
    - Observability (logs/agent.log)
    - Strict JSON pipeline (backend-friendly)
    """
    setup_logging()
    logging.info("GiftGenie CLI run started.")

    session_state: Dict[str, Any] = {
        "persona_profile": None,
        "initial_gifts": None,
        "final_gifts": None,
        "chosen_gift": None,
    }

    memory = load_memory()
    print_memory_summary(memory)

    try:
        model = setup_gemini()
    except RuntimeError as e:
        logging.error("Gemini setup failed: %s", e)
        print("\n[ERROR] Gemini setup failed:")
        print(e)
        return

    final_gifts = orchestrator_agent(model, session_state)

    print("🎁 Final Budget-Aware Gift Ideas:\n")
    for idx, g in enumerate(final_gifts, start=1):
        print(f"{idx}. {g['title']}  ({g.get('priceRange', '').strip()})")
        if g.get("reason"):
            print(f"   {g['reason']}")
        print()

    print("\nIf you like one of these ideas, you can save it so GiftGenie remembers it next time.")
    chosen_gift = input(
        "Type the name or short description of the gift you chose (or press Enter to skip): "
    ).strip()

    if chosen_gift:
        session_state["chosen_gift"] = chosen_gift
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "persona_profile": session_state.get("persona_profile", {}),
            "chosen_gift": chosen_gift,
            "notes": "Saved from CLI session",
        }
        append_memory_entry(entry)
        print("\n💾 Saved your choice to long-term memory.")
        logging.info("User saved chosen gift: %s", chosen_gift)
    else:
        print("\nNo gift choice saved this time.")
        logging.info("No gift choice saved for this session.")

    print("\nThanks for using GiftGenie (multi-agent + tool + memory + logging).\n")
    logging.info("GiftGenie CLI run finished.")


if __name__ == "__main__":
    main()
