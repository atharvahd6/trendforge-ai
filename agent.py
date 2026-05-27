import os
import time
from google import genai
from google.genai import types

def get_gemini_client():
    # Uses your existing GEMINI_API_KEY
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def call_trend_scout(client):
    idea_file = "INPUT_IDEA.txt"
    if os.path.exists(idea_file) and os.path.getsize(idea_file) > 10:
        with open(idea_file, "r", encoding="utf-8") as f:
            user_idea = f.read().strip()
        with open(idea_file, "w", encoding="utf-8") as f: f.write("")
        return f"PRODUCT: {user_idea}"

    scout_prompt = "Identify a high-value professional bottleneck. Output: PRODUCT NAME, PROBLEM SOLVED, CORE UTILITY."
    response = client.models.generate_content(model='gemini-2.0-flash', contents=scout_prompt)
    return response.text

def call_core_developer(client, scout_output):
    print("DEBUG: Generating code using Gemini...")
    prompt = f"""
    Review this analysis:
    {scout_output}
    
    Write complete, production-ready, beautiful, single-file HTML/CSS/JS code.
    - Style it professionally (clean, modern, mobile-friendly).
    - No frameworks (plain HTML/CSS/JS only).
    - Include a 'Buy Source Code' button at the bottom.
    - Output ONLY the raw HTML code (do not wrap in markdown or code blocks).
    """
    
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return response.text.strip().replace("```html", "").replace("```", "").strip()

def main():
    client = get_gemini_client()
    scout_data = call_trend_scout(client)
    code = call_core_developer(client, scout_data)
    
    product_name = "tool-" + str(int(time.time()))
    os.makedirs(f"products/{product_name}", exist_ok=True)
    
    with open(f"products/{product_name}/index.html", "w", encoding="utf-8") as f:
        f.write(code)
    print(f"SUCCESS: Deployed to products/{product_name}/index.html")

if __name__ == "__main__":
    main()
