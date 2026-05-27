import os
import time
from google import genai
from openai import OpenAI

def get_api_clients():
    clients = {}
    if os.environ.get("OPENAI_API_KEY"):
        clients["openai"] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if os.environ.get("GEMINI_API_KEY"):
        clients["gemini"] = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return clients

def call_trend_scout(clients):
    idea_file = "INPUT_IDEA.txt"
    
    # 1. Check for manual idea
    if os.path.exists(idea_file) and os.path.getsize(idea_file) > 10:
        with open(idea_file, "r", encoding="utf-8") as f:
            user_idea = f.read().strip()
        print(f"DEBUG: Manual Idea Detected: {user_idea[:50]}...")
        
        # Clear the file
        with open(idea_file, "w", encoding="utf-8") as f: f.write("")
        return f"PRODUCT NAME: Custom Tool\nPROBLEM SOLVED: {user_idea}\nCORE UTILITY: Build a professional, single-file HTML/CSS/JS tool based on these requirements."

    # 2. Automated Scouting if no input
    print("DEBUG: No manual idea. Running autonomous scout...")
    if "gemini" in clients:
        scout_prompt = "Identify a high-value professional bottleneck. Output: PRODUCT NAME, PROBLEM SOLVED, CORE UTILITY."
        return clients["gemini"].models.generate_content(model='gemini-2.0-flash', contents=scout_prompt).text.strip()
    
    return "PRODUCT NAME: Default Tool\nPROBLEM SOLVED: Productivity\nCORE UTILITY: Basic utility."

def call_core_developer(clients, scout_output):
    print("DEBUG: Generating code...")
    prompt = f"Review this analysis:\n{scout_output}\n\nWrite complete, production-ready, beautifully styled, single-file HTML/CSS/JS code. Include a 'Buy Source Code' button. Output ONLY the code starting with <html> and ending with </html>."
    
    if "openai" in clients:
        response = clients["openai"].chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip("`").replace("html", "").strip()
    return "<html>Error: No AI model available.</html>"

def main():
    clients = get_api_clients()
    scout_data = call_trend_scout(clients)
    
    # Generate the product
    code = call_core_developer(clients, scout_data)
    
    # Save the file
    product_name = "custom-tool-" + str(int(time.time()))
    os.makedirs(f"products/{product_name}", exist_ok=True)
    
    with open(f"products/{product_name}/index.html", "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"SUCCESS: Tool deployed to products/{product_name}/index.html")

if __name__ == "__main__":
    main()
