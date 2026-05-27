import os
import time
from google import genai
from groq import Groq
from mistralai.client import Mistral

def get_clients():
    """Initializes all available AI clients."""
    return {
        "gemini": genai.Client(api_key=os.environ.get("GEMINI_API_KEY")),
        "groq": Groq(api_key=os.environ.get("GROQ_API_KEY")),
        "mistral": Mistral(api_key=os.environ.get("MISTRAL_API_KEY")),
    }

def get_scout_prompt():
    """Persona for the problem-scouting agent."""
    return """
    Act as a professional Trend Analyst. Identify one high-value, specific professional 
    bottleneck that professionals in India currently face. 
    Output the result in this exact format:
    PRODUCT NAME: [A catchy name]
    PROBLEM SOLVED: [Detailed description of the problem]
    CORE UTILITY: [Description of the HTML tool to be built]
    """

def call_ai_with_fallback(clients, task_prompt):
    """Attempts the task on multiple providers until one succeeds."""
    
    # 1. Try Gemini
    try:
        print("DEBUG: Trying Gemini...")
        response = clients["gemini"].models.generate_content(
            model='gemini-2.0-flash', contents=task_prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini failed: {e}")

    # 2. Try Groq
    try:
        print("DEBUG: Falling back to Groq...")
        response = clients["groq"].chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": task_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq failed: {e}")

    # 3. Try Mistral
    try:
        print("DEBUG: Falling back to Mistral...")
        response = clients["mistral"].chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": task_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"All AI providers failed: {e}")
        return "<html>Error: Factory currently offline.</html>"

def main():
    clients = get_clients()
    idea_file = "INPUT_IDEA.txt"
    
    # Check for manual input
    if os.path.exists(idea_file) and os.path.getsize(idea_file) > 10:
        with open(idea_file, "r", encoding="utf-8") as f:
            user_idea = f.read().strip()
        with open(idea_file, "w", encoding="utf-8") as f: f.write("")
        task = f"Build this tool: {user_idea}. Output ONLY raw HTML/CSS/JS."
    else:
        # AUTONOMOUS SCOUTING MODE
        print("DEBUG: No manual input. Scouting for problems...")
        scout_info = call_ai_with_fallback(clients, get_scout_prompt())
        task = f"Build a tool based on this: {scout_info}. Output ONLY raw HTML/CSS/JS (no markdown)."

    # Execute generation
    code = call_ai_with_fallback(clients, task)
    
    # Clean output
    code = code.replace("```html", "").replace("```", "").strip()
    
    # Save output
    product_name = f"tool-{int(time.time())}"
    os.makedirs(f"products/{product_name}", exist_ok=True)
    with open(f"products/{product_name}/index.html", "w", encoding="utf-8") as f:
        f.write(code)
        
    print(f"SUCCESS: Deployed to products/{product_name}/index.html")

if __name__ == "__main__":
    main()
