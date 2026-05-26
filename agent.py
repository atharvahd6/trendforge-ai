import os
import sys
from datetime import datetime
from google import genai
from openai import OpenAI
import cohere
from mistralai.client import Mistral

def get_api_clients():
    """Securely initialize all 6 available AI frameworks with structural fallbacks"""
    clients = {}
    if os.environ.get("OPENAI_API_KEY"):
        try: clients["openai"] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except: print("⚠️ OpenAI client setup failed.")
    if os.environ.get("GEMINI_API_KEY"):
        try: clients["gemini"] = genai.Client()
        except: print("⚠️ Gemini configuration failed.")
    if os.environ.get("GROQ_API_KEY"):
        try: clients["groq"] = OpenAI(api_key=os.environ.get("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
        except: print("⚠️ Groq client setup failed.")
    if os.environ.get("COHERE_API_KEY"):
        try: clients["cohere"] = cohere.ClientV2(api_key=os.environ.get("COHERE_API_KEY"))
        except: print("⚠️ Cohere client setup failed.")
    if os.environ.get("MISTRAL_API_KEY"):
        try: clients["mistral"] = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
        except: print("⚠️ Mistral client setup failed.")
    if os.environ.get("GITHUB_TOKEN"):
        try: clients["github"] = OpenAI(api_key=os.environ.get("GITHUB_TOKEN"), base_url="https://models.inference.ai.azure.com")
        except: print("⚠️ GitHub Native Token client setup failed.")
    return clients

# --- PHASE 1: THE PRODUCT SCOUT ---
def call_trend_scout(clients):
    scout_prompt = (
        "Identify one hyper-specific, high-demand web utility tool or mini web app that can run "
        "COMPLETELY inside a single index.html file using native frontend JavaScript (e.g., an advanced "
        "CSS grid generator, an interactive SVG path optimizer, a programmatic regex visualizer, etc.). "
        "Output EXACTLY in this format:\n"
        "PRODUCT NAME: [Clean Name]\n"
        "CORE UTILITY: [1 sentence explaining exactly what frontend calculation or problem it solves instantly]"
    )
    if os.path.exists("manual_ideas.txt"):
        with open("manual_ideas.txt", "r", encoding="utf-8") as f:
            manual_content = f.read().strip()
        if manual_content: return manual_content

    if "gemini" in clients:
        try:
            res = clients["gemini"].models.generate_content(model="gemini-2.5-flash", contents=scout_prompt)
            return res.text.strip()
        except: pass
    if "openai" in clients:
        try:
            res = clients["openai"].chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": scout_prompt}])
            return res.choices[0].message.content.strip()
        except: pass
    if "github" in clients:
        res = clients["github"].chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": scout_prompt}])
        return res.choices[0].message.content.strip()
    raise Exception("Scouting engine failure.")

# --- PHASE 2: THE CODER (Generates the 100% finished tool) ---
def call_core_developer(clients, scout_output):
    prompt = (
        f"Based on this product layout:\n{scout_output}\n\n"
        "Write the absolute complete, production-ready, beautiful, modern, single-file HTML/CSS/JS source code for this tool. "
        "It must be 100% functional immediately when opened in a browser. Include an embedded sleek dark-mode UI layout, "
        "all calculation algorithms, and a prominent call-to-action banner button tracking premium subscriptions. "
        "Do not use placeholders, do not omit scripts, and do not use markdown codeblocks inside your actual app code. "
        "Output ONLY the complete code starting with <!DOCTYPE html> and ending with </html>."
    )
    # Using OpenAI/GitHub GPT-4o as primary for heavy code synthesis
    for provider in ["openai", "github", "mistral"]:
        if provider in clients:
            try:
                model_name = "gpt-4o" if provider == "openai" or provider == "github" else "mistral-large-latest"
                res = clients[provider].chat.completions.create(
                    model=model_name, messages=[{"role": "user", "content": prompt}]
                ) if provider != "mistral" else clients["mistral"].chat.complete(model=model_name, messages=[{"role": "user", "content": prompt}])
                
                content = res.choices[0].message.content.strip() if provider != "mistral" else res.choices[0].message.content.strip()
                if "```html" in content:
                    content = content.split("```html")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                return content
            except: pass
    raise Exception("Code generation failure.")

# --- PHASE 3: THE PERSONAL BRAND MARKETER (Generates ready-to-use social posts) ---
def call_personal_marketer(clients, scout_output):
    prompt = (
        f"Review this tool concept:\n{scout_output}\n\n"
        "Write one highly engaging, high-converting Twitter/X thread (3 tweets) and one professional LinkedIn post "
        "designed to be published directly from the founder's personal account. It must sound completely human, data-driven, "
        "and authoritative. Highlight the exact professional problem solved and direct readers to check out the live tool link. "
        "DO NOT mention AI, AI agents, automated loops, or automated workflows. Output cleanly under clear headers."
    )
    if "groq" in clients:
        try:
            res = clients["groq"].chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
            return res.choices[0].message.content.strip()
        except: pass
    if "openai" in clients:
        try:
            res = clients["openai"].chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
            return res.choices[0].message.content.strip()
        except: pass
    return "Marketing assets generation bypassed safely."

# --- CORE INTEGRATION ENGINE ---
def main():
    current_date = datetime.now().strftime("%Y-%m-%d")
    clients = get_api_clients()
    
    try:
        scout_data = call_trend_scout(clients)
        functional_code = call_core_developer(clients, scout_data)
        social_distribution = call_personal_marketer(clients, scout_data)
        
        prod_name = "Automated Utility"
        for line in scout_data.split("\n"):
            if "PRODUCT NAME:" in line:
                prod_name = line.replace("PRODUCT NAME:", "").strip()
        
        clean_folder_name = "".join(c for c in prod_name if c.isalnum() or c in (' ', '_', '-')).rstrip().lower().replace(" ", "-")
        target_dir = f"products/{clean_folder_name}"
        os.makedirs(target_dir, exist_ok=True)
        
        # Save the 100% finished product ready to be served immediately by GitHub Pages
        with open(f"{target_dir}/index.html", "w", encoding="utf-8") as f:
            f.write(functional_code)
            
        # Save marketing copy assets to the archived historical system records
        os.makedirs("archived_trends", exist_ok=True)
        with open(f"archived_trends/launch_kit_{current_date}.md", "w", encoding="utf-8") as f:
            f.write(f"# 🚀 Complete Product Launch Kit ({current_date})\n\n## 💡 Discovered Concept\n{scout_data}\n\n## 📋 Personal Distribution Copy\n{social_distribution}\n\n## 🛠️ Generated Application Directory Path\n`/{target_dir}/index.html`")
            
        # Update your running dashboard timeline index
        live_app_link = f"https://atharvahd6.github.io/trendforge-ai/products/{clean_folder_name}/"
        journal_entry = f"| {current_date} | **{prod_name}** | [Launch App Tool 🌐]({live_app_link}) | [View Promotion Copy 📄](archived_trends/launch_kit_{current_date}.md) |\n"
        
        if not os.path.exists("MASTER_TREND_JOURNAL.md"):
            with open("MASTER_TREND_JOURNAL.md", "w", encoding="utf-8") as f:
                f.write("# 📚 Master Autonomous Trend Journal\n\n| Date Run | Discovered Startup Concept | Live Web App Link | Strategic Copy Package |\n| :--- | :--- | :--- | :--- |\n")
                
        with open("MASTER_TREND_JOURNAL.md", "a", encoding="utf-8") as f:
            f.write(journal_entry)
            
        print("🏁 Operational cycle complete! Product deployed completely.")
    except Exception as e:
        print(f"❌ Operation terminated prematurely: {e}")

if __name__ == "__main__":
    main()
