import os
import time
from google import genai
from groq import Groq
from mistralai import Mistral  # Adjusted import style based on modern SDK versions

def get_clients():
    """Initializes available AI clients safely."""
    return {
        "gemini": genai.Client(api_key=os.environ.get("GEMINI_API_KEY")) if os.environ.get("GEMINI_API_KEY") else None,
        "groq": Groq(api_key=os.environ.get("GROQ_API_KEY")) if os.environ.get("GROQ_API_KEY") else None,
        "mistral": Mistral(api_key=os.environ.get("MISTRAL_API_KEY")) if os.environ.get("MISTRAL_API_KEY") else None,
    }

def get_scout_prompt():
    """Persona for the problem-scouting agent."""
    return """
    Act as a professional software product manager. Identify one high-value 
    problem that could be solved by an offline Python desktop application.
    Output in this format:
    PRODUCT NAME: [Name]
    PROBLEM SOLVED: [Description]
    CORE UTILITY: [Features to implement]
    """

def call_ai_with_fallback(clients, task_prompt):
    """Attempts the task on multiple providers until one succeeds."""
    
    # 1. Try Gemini
    if clients.get("gemini"):
        try:
            print("DEBUG: Trying Gemini...")
            response = clients["gemini"].models.generate_content(
                model='gemini-2.0-flash', contents=task_prompt
            )
            if response.text:
                return response.text
        except Exception as e:
            print(f"Gemini failed: {e}")

    # 2. Try Groq
    if clients.get("groq"):
        try:
            print("DEBUG: Falling back to Groq...")
            response = clients["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": task_prompt}]
            )
            if response.choices[0].message.content:
                return response.choices[0].message.content
        except Exception as e:
            print(f"Groq failed: {e}")

    # 3. Try Mistral
    if clients.get("mistral"):
        try:
            print("DEBUG: Falling back to Mistral...")
            response = clients["mistral"].chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": task_prompt}]
            )
            if response.choices[0].message.content:
                return response.choices[0].message.content
        except Exception as e:
            print(f"Mistral failed: {e}")

    print("CRITICAL: All AI providers failed to return a response.")
    return None

def main():
    clients = get_clients()
    idea_file = "INPUT_IDEA.txt"
    is_manual = False
    
    # Check for manual input
    if os.path.exists(idea_file) and os.path.getsize(idea_file) > 10:
        print("DEBUG: Found manual input. Processing...")
        with open(idea_file, "r", encoding="utf-8") as f:
            user_idea = f.read().strip()
        task = f"Build a Python/Tkinter desktop app for: {user_idea}. Use subprocess to call Ollama. Output ONLY raw Python code."
        is_manual = True
    else:
        # AUTONOMOUS SCOUTING MODE
        print("DEBUG: No manual input or file empty. Scouting for problems...")
        scout_info = call_ai_with_fallback(clients, get_scout_prompt())
        if not scout_info:
            print("Aborting execution: Could not scout a new idea because all APIs are down.")
            return
        task = f"Build a Python/Tkinter desktop app based on this requirement: {scout_info}. Use subprocess to call Ollama. Output ONLY raw Python code (no markdown)."

    # Execute generation
    code = call_ai_with_fallback(clients, task)
    
    if not code:
        print("Aborting execution: Failed to generate code from any provider.")
        return
        
    # Clean output (remove markdown code blocks safely)
    code = code.replace("```python", "").replace("```", "").strip()
    
    # Save as .py
    product_name = f"desktop-tool-{int(time.time())}"
    os.makedirs(f"products/{product_name}", exist_ok=True)
    with open(f"products/{product_name}/assistant.py", "w", encoding="utf-8") as f:
        f.write(code)
        
    print(f"SUCCESS: Desktop tool deployed to products/{product_name}/assistant.py")

    # ONLY clear the manual file if the script actually successfully wrote the output
    if is_manual:
        with open(idea_file, "w", encoding="utf-8") as f: 
            f.write("")
        print("DEBUG: Input file cleared safely.")

if __name__ == "__main__":
    main()
