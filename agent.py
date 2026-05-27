import os
import time
import random
from google import genai
from openai import OpenAI
from groq import Groq
from mistralai import Mistral

def get_clients():
    """Initializes all available AI clients."""
    return {
        "gemini": genai.Client(api_key=os.environ.get("GEMINI_API_KEY")),
        "groq": Groq(api_key=os.environ.get("GROQ_API_KEY")),
        "mistral": Mistral(api_key=os.environ.get("MISTRAL_API_KEY")),
    }

def call_ai_with_fallback(clients, task_prompt):
    """Attempts the task on multiple providers until one succeeds."""
    
    # 1. Try Gemini (Flash 2.0)
    try:
        print("DEBUG: Trying Gemini...")
        response = clients["gemini"].models.generate_content(
            model='gemini-2.0-flash', contents=task_prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini failed: {e}")

    # 2. Try Groq (Llama 3 - Ultra Fast)
    try:
        print("DEBUG: Falling back to Groq...")
        response = clients["groq"].chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": task_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq failed: {e}")

    # 3. Try Mistral (Reliable)
    try:
        print("DEBUG: Falling back to Mistral...")
        response = clients["mistral"].chat.completions.create(
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
        task = "Identify a high-value professional bottleneck and write complete, single-file HTML code for a tool that solves it."

    # Execute generation with self-healing fallback
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
