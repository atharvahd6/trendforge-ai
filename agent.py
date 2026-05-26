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
    raise Exception("Scouting engine failure.")

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

# --- NEW EXTENSION: FORCE REWRITE MAIN INDEX.HTML FILE ---
def update_root_index():
    """Reads the markdown journal table, converts it safely to clean HTML rows, and forces a write to index.html"""
    if not os.path.exists("MASTER_TREND_JOURNAL.md"):
        return
        
    with open("MASTER_TREND_JOURNAL.md", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    html_table_rows = ""
    for line in lines:
        clean_line = line.strip()
        # Skip headers, divider lines, and empty spaces safely
        if not clean_line.startswith("|") or "Date Run" in clean_line or ":---" in clean_line:
            continue
            
        # Split columns and filter out edge spaces
        parts = [p.strip() for p in clean_line.split("|")[1:-1]]
        
        # 🔑 THE SAFETY GUARD: Ensure the row has all 4 columns before reading indexes
        if len(parts) >= 4:
            date_str = parts[0]
            name_str = parts[1].replace("**", "")
            
            # Extract links safely from markdown formats [Text](URL)
            app_link = "#"
            if "](" in parts[2]:
                app_link = parts[2].split("](")[1].split(")")[0]
                
            promo_link = "#"
            if "](" in parts[3]:
                promo_link = parts[3].split("](")[1].split(")")[0]
                
            html_table_rows += f"""
            <tr>
                <td>{date_str}</td>
                <td style="font-weight:600; color:#fff;">{name_str}</td>
                <td><a href="{app_link}" target="_blank" style="color:#10B981; text-decoration:none; font-weight:bold;">Launch App Tool 🌐</a></td>
                <td><a href="{promo_link}" target="_blank" style="color:#818CF8; text-decoration:none;">View Promo Copy 📄</a></td>
            </tr>"""

    index_layout = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrendForge Venture Lab</title>
    <style>
        :root {{
            --bg-main: #0B0F19;
            --bg-card: #151D30;
            --accent: #38BDF8;
            --text-main: #F3F4F6;
            --text-muted: #9CA3AF;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            margin: 0; padding: 0; line-height: 1.6;
        }}
        header {{
            max-width: 1100px; margin: 0 auto; padding: 4rem 2rem 2rem 2rem; text-align: center;
        }}
        h1 {{
            font-size: 3rem; font-weight: 800; margin-bottom: 0.5rem;
            background: linear-gradient(to right, #38BDF8, #818CF8);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: var(--text-muted); font-size: 1.2rem; max-width: 700px; margin: 0 auto; }}
        main {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
        .table-container {{
            background-color: var(--bg-card); border-radius: 12px; padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.05); overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        th {{ color: var(--accent); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em; }}
    </style>
</head>
<body>
    <header>
        <h1>TrendForge Venture Lab</h1>
        <p class="subtitle">Every 24 hours, this lab deploys a 100% complete, functional, ready-to-use web tool to solve real digital constraints immediately.</p>
    </header>
    <main>
        <h2 style="font-size:1.5rem; margin-bottom:1rem;">📚 Live Operational Product Ledger</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date Run</th>
                        <th>Discovered Startup Concept</th>
                        <th>Live Web App Link</th>
                        <th>Strategic Copy Package</th>
                    </tr>
                </thead>
                <tbody>
                    {html_table_rows if html_table_rows else "<tr><td colspan='4' style='color:var(--text-muted); text-align:center;'>Initializing deployment matrices...</td></tr>"}
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_layout)
