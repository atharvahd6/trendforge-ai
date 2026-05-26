import os
import sys
from datetime import datetime
from google import genai
from openai import OpenAI
import cohere
from mistralai.client import Mistral

def get_api_clients():
    """Initialize all available AI frameworks securely"""
    clients = {}
    if os.environ.get("OPENAI_API_KEY"):
        try: clients["openai"] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except: pass
    if os.environ.get("GEMINI_API_KEY"):
        try: clients["gemini"] = genai.Client()
        except: pass
    if os.environ.get("GROQ_API_KEY"):
        try: clients["groq"] = OpenAI(api_key=os.environ.get("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
        except: pass
    if os.environ.get("COHERE_API_KEY"):
        try: clients["cohere"] = cohere.ClientV2(api_key=os.environ.get("COHERE_API_KEY"))
        except: pass
    if os.environ.get("MISTRAL_API_KEY"):
        try: clients["mistral"] = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
        except: pass
    if os.environ.get("GITHUB_TOKEN"):
        try: clients["github"] = OpenAI(api_key=os.environ.get("GITHUB_TOKEN"), base_url="https://models.inference.ai.azure.com")
        except: pass
    return clients

# --- PHASE 1: AUTONOMOUS REAL-WORLD PROBLEM SCOUT ---
def call_trend_scout(clients):
    scout_prompt = (
        "Identify one highly frustrating, repetitive, real-world daily problem faced by normal individuals "
        "hundreds of times a year (e.g., invoice sorting, personal budgeting friction, email cleanups, text conversions, layout math). "
        "It must be something that can be solved instantly inside a single web-browser page using pure frontend JavaScript code. "
        "Output EXACTLY in this format:\n"
        "PRODUCT NAME: [Clean Title]\n"
        "PROBLEM SOLVED: [1 sentence explaining the specific individual pain point]\n"
        "CORE UTILITY: [1 sentence explaining the exact functional logic the app will execute to solve it]"
    )
    
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
    raise Exception("Scouting engine failure. Check API key configurations.")

# --- PHASE 2: AUTOMATED WEB APP DEVELOPER ---
def call_core_developer(clients, scout_output):
    prompt = (
        f"Review this autonomous problem scout analysis:\n{scout_output}\n\n"
        "You are the Core Software Engineer. Write the absolute complete, production-ready, beautifully styled, single-file "
        "HTML/CSS/JS source code that builds this tool completely for the customer. "
        "Requirements:\n"
        "- It must be 100% functional, calculation-ready, or text-processing complete immediately when opened.\n"
        "- Embed an elegant, modern dark-mode user interface.\n"
        "- Do not include placeholders, do not leave code sections incomplete, and do not say 'add your logic here'.\n"
        "- Include a clear, beautiful premium upgrade feature banner or modal prompt at the bottom to collect subscription test clicks.\n"
        "Output ONLY the raw code starting with <!DOCTYPE html> and ending with </html>."
    )
    
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
    raise Exception("Production code synthesis engine failed.")

# --- PHASE 3: THE PERSONAL ACCOUNT MARKETER ---
def call_personal_marketer(clients, scout_output):
    prompt = (
        f"Review this tool configuration:\n{scout_output}\n\n"
        "Write one engaging Twitter/X thread (3 tweets) and one authoritative LinkedIn post "
        "written directly from the founder's personal perspective. Highlight the massive individual problem solved, "
        "the time saved, and tell them to check out the live utility link. "
        "CRITICAL: Do not mention AI, do not mention automated scripts, do not mention agents. It must look 100% human-built. "
        "Output cleanly with headers."
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
    return "Marketing templates automatically generated via internal fallback."

# --- MAIN ORCHESTRATION ENGINE ---
def main():
    current_date = datetime.now().strftime("%Y-%m-%d")
    clients = get_api_clients()
    
    try:
        # 1. AI automatically scouts a real world problem on its own
        scout_data = call_trend_scout(clients)
        
        # 2. AI automatically codes the complete, ready-to-use application
        functional_code = call_core_developer(clients, scout_data)
        
        # 3. AI automatically drafts your personal promotional posts
        social_distribution = call_personal_marketer(clients, scout_data)
        
        prod_name = "Autonomous Tool"
        for line in scout_data.split("\n"):
            if "PRODUCT NAME:" in line:
                prod_name = line.replace("PRODUCT NAME:", "").strip()
        
        clean_folder_name = "".join(c for c in prod_name if c.isalnum() or c in (' ', '_', '-')).rstrip().lower().replace(" ", "-")
        target_dir = f"products/{clean_folder_name}"
        os.makedirs(target_dir, exist_ok=True)
        
        # Write the functional customer-facing app file
        with open(f"{target_dir}/index.html", "w", encoding="utf-8") as f:
            f.write(functional_code)
            
        # Write marketing assets for your personal records
        os.makedirs("archived_trends", exist_ok=True)
        with open(f"archived_trends/launch_kit_{current_date}.md", "w", encoding="utf-8") as f:
            f.write(f"# 🚀 Autonomous Launch Kit ({current_date})\n\n## 💡 Independent Analysis\n{scout_data}\n\n## 📋 Personal Account Promo Scripts\n{social_distribution}\n\n## 🛠️ Deployed File Location\n`/{target_dir}/index.html`")
            
        # Push variables to your central master journal dashboard link
        live_app_link = f"https://atharvahd6.github.io/trendforge-ai/products/{clean_folder_name}/"
        journal_entry = f"| {current_date} | **{prod_name}** | [Open Live App Tool 🌐]({live_app_link}) | [View Promotion Copy 📄](archived_trends/launch_kit_{current_date}.md) |\n"
        
        if not os.path.exists("MASTER_TREND_JOURNAL.md"):
            with open("MASTER_TREND_JOURNAL.md", "w", encoding="utf-8") as f:
                f.write("# 📚 Master Autonomous Trend Journal\n\n| Date Run | Discovered Startup Concept | Live Web App Link | Strategic Copy Package |\n| :--- | :--- | :--- | :--- |\n")
                
        with open("MASTER_TREND_JOURNAL.md", "a", encoding="utf-8") as f:
            f.write(journal_entry)
            
        print("🏁 Operational cycle complete! Product deployed completely.")
    except Exception as e:
        print(f"❌ Operation terminated: {e}")

if __name__ == "__main__":
    main()
