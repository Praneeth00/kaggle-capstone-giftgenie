import os
import textwrap

try:
    from google import generativeai as genai
except ImportError:
    genai = None


def setup_gemini():
    """
    Configure the Gemini client using an environment variable.
    Make sure you set GEMINI_API_KEY in your system before running:

        export GEMINI_API_KEY="your-key-here"    (macOS/Linux)
        set GEMINI_API_KEY="your-key-here"       (Windows cmd)
        $env:GEMINI_API_KEY="your-key-here"      (PowerShell)
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
    # You can change the model name based on what you use in the course
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model


def collect_user_inputs():
    """
    Ask the user basic questions about the gift.
    This is intentionally simple for Step 2.
    """
    print("🎁 Welcome to GiftGenie (Step 2 baseline)\n")

    recipient_name = input("Who is this gift for? (e.g., my sister, my manager): ").strip()
    age = input("Approximate age? (e.g., 10, 25, 40s): ").strip()
    relationship = input("Relationship? (e.g., friend, cousin, coworker): ").strip()
    occasion = input("What is the occasion? (e.g., birthday, promotion, thank you): ").strip()
    budget = input("What is your budget? (e.g., 25, 50-75): ").strip()
    interests = input("What do they like? (e.g., books, games, travel, plants): ").strip()
    dislikes = input("Anything to avoid? (e.g., alcohol, tech, perfumes) [optional]: ").strip()

    return {
        "recipient_name": recipient_name or "the recipient",
        "age": age or "unknown",
        "relationship": relationship or "friend",
        "occasion": occasion or "special occasion",
        "budget": budget or "flexible",
        "interests": interests or "general interests",
        "dislikes": dislikes or "none specified",
    }


def build_prompt(info: dict) -> str:
    """
    Turn the answers into a structured prompt for Gemini.
    """
    prompt = f"""
    You are an expert gift concierge.

    Please suggest 5 thoughtful, specific gift ideas for the following recipient:

    - Who: {info['recipient_name']}
    - Age: {info['age']}
    - Relationship: {info['relationship']}
    - Occasion: {info['occasion']}
    - Budget: {info['budget']} (in USD or equivalent)
    - Interests: {info['interests']}
    - Things to avoid: {info['dislikes']}

    Requirements:
    - Return exactly 5 ideas.
    - For each idea, give:
        - A short name
        - 1–2 sentence explanation of why it fits
        - A rough price range
    - Vary the types of gifts (not all tech, not all gift cards).
    - Keep the tone friendly and concise.
    """

    # Clean up leading whitespace
    return textwrap.dedent(prompt).strip()


def get_gift_ideas(model, prompt: str) -> str:
    """
    Call Gemini with the prompt and return the text response.
    """
    print("\n✨ Asking Gemini for gift ideas...\n")

    response = model.generate_content(prompt)
    # Depending on the SDK version, the property may be .text or .candidates[…]
    try:
        return response.text
    except AttributeError:
        # Very simple fallback; adjust if your course teaches a specific pattern
        return str(response)


def main():
    # 1. Set up Gemini
    try:
        model = setup_gemini()
    except RuntimeError as e:
        print("\n[ERROR] Gemini setup failed:")
        print(e)
        return

    # 2. Collect inputs from user
    info = collect_user_inputs()

    # 3. Build the prompt
    prompt = build_prompt(info)

    # (Optional) print the prompt for debugging
    # print("\n--- Prompt sent to Gemini ---")
    # print(prompt)
    # print("-----------------------------\n")

    # 4. Get gift ideas from Gemini
    ideas_text = get_gift_ideas(model, prompt)

    # 5. Display the results nicely
    print("🎁 Suggested Gift Ideas:\n")
    print(ideas_text)
    print("\nThanks for using GiftGenie (baseline). In the next steps we'll add:")
    print("- Multi-agent flow (profiling agent + ideas agent + filter agent)")
    print("- Tools (price filter, search)")
    print("- Memory of past gifts\n")


if __name__ == "__main__":
    main()
