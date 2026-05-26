import os
import sys
import time
from datetime import datetime
from google import genai
from openai import OpenAI
from mistralai.client import Mistral

def get_api_clients():
    clients = {}
    if os.environ.get("OPENAI_API_KEY"):
        try: clients["openai"] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except: pass
    if os.environ.get("GEMINI_API_KEY"):
        try: clients["gemini"] = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        except: pass
    if os.environ.get("MISTRAL_API_KEY"):
        try: clients["mistral"] = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
        except: pass
    return clients

def call_trend_scout(clients):
    # --- PIPELINE INJECTION: CHECK FOR MANUAL IDEA FIRST ---
    if os.path.exists("INPUT_IDEA.txt") and os.path.getsize("INPUT_IDEA.txt") > 0:
        with open("INPUT_IDEA.txt", "r", encoding="utf-8") as f:
            user_idea = f.read().strip()
        with open("INPUT_IDEA.txt", "w", encoding="utf-8") as f: f.write("") # Clear file
        return f"PRODUCT NAME: Custom Tool\nPROBLEM SOLVED: {user_idea}\nCORE UTILITY: Build a professional tool that solves the specific problem requested by the user."
    
    # --- AUTOMATED SCOUTING ---
    scout_prompt = (
        "Identify a high-value professional bottleneck (e.g., tax calculation, invoice extraction). "
        "Output: PRODUCT NAME, PROBLEM SOLVED, CORE UTILITY."
    )
    if "gemini" in clients:
        try: return clients["gemini"].models.generate_content(model='gemini-2.5-flash', contents=scout_prompt).text.strip()
        except: pass
    return "PRODUCT NAME: Default Tool\nPROBLEM SOLVED: Generic efficiency.\nCORE UTILITY: Simple calculation utility."

def call_core_developer(clients, scout_output):
    prompt = f"Review this analysis:\n{scout_output}\n\nWrite complete, production-ready, beautifully styled, single-file HTML/CSS/JS code. Include a 'Buy Source Code' button linked to your payment platform. Output ONLY raw code."
    # ... (Rest of your existing developer logic)
    # [Keep your existing code generation implementation here]
    return "<html>...</html>" # Placeholder for your generated code logic

def update_root_index():
    # ... (Your existing 3-column table logic)
    pass

def main():
    clients = get_api_clients()
    scout_data = call_trend_scout(clients)
    functional_code = call_core_developer(clients, scout_data)
    # ... (Rest of your deployment logic)
    print("🏁 Operational cycle complete!")

if __name__ == "__main__": main()
