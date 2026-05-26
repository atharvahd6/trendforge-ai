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
    scout_prompt = (
        "Identify a high-value, repetitive professional bottleneck or personal friction point (e.g., "
        "calculating specific tax/loan scenarios, automating invoice data extraction, complex unit conversion "
        "tools for tradesmen, or scheduling optimization logic). "
        "CRITICAL: Do NOT suggest simple text formatting or 'cleaners'. It must be a tool that solves a "
        "measurable pain point where a user would willingly pay a subscription to save 2 hours of manual work. "
        "Output EXACTLY in this format:\n"
        "PRODUCT NAME: [Clean Title]\n"
        "PROBLEM SOLVED: [1 sentence explaining the specific professional pain point]\n"
        "CORE UTILITY: [1 sentence explaining the exact functional logic the app will execute to solve it]"
    )
    if "gemini" in clients:
        for attempt in range(1, 4):
            try:
                res = clients["gemini"].models.generate_content(model='gemini-2.5-flash', contents=scout_prompt)
                return res.text.strip()
            except: time.sleep(5)
    if "mistral" in clients:
        try: return clients["mistral"].chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": scout_prompt}]).choices[0].message.content.strip()
        except: pass
    raise Exception("Scout failed.")

def call_core_developer(clients, scout_output):
    prompt = (
        f"Review this scout analysis:\n{scout_output}\n\n"
        "Write complete, production-ready, beautifully styled, single-file HTML/CSS/JS source code. "
        "Requirements:\n"
        "- 100% functional, calculation-ready tool.\n"
        "- Modern dark-mode UI.\n"
        "- Include a clear 'Upgrade Now' premium banner that triggers a subscription modal ($9/mo).\n"
        "Output ONLY raw code, no markdown blocks."
    )
    for provider in ["gemini", "mistral", "openai"]:
        try:
            if provider == "gemini": content = clients["gemini"].models.generate_content(model="gemini-2.5-flash", contents=prompt).text.strip()
            elif provider == "mistral": content = clients["mistral"].chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}]).choices[0].message.content.strip()
            else: continue
            return content.replace("```html", "").replace("```", "").strip()
        except: continue
    raise Exception("Code generation failed.")

def update_root_index():
    if not os.path.exists("MASTER_TREND_JOURNAL.md"): return
    with open("MASTER_TREND_JOURNAL.md", "r", encoding="utf-8") as f: lines = f.readlines()
    html_table_rows = ""
    for line in lines:
        clean_line = line.strip()
        if not clean_line.startswith("|") or "Date" in clean_line or ":---" in clean_line: continue
        parts = [p.strip() for p in clean_line.split("|")[1:-1]]
        if len(parts) >= 3:
            html_table_rows += f"<tr><td>{parts[0]}</td><td style='font-weight:600; color:#fff;'>{parts[1].replace('**', '')}</td><td><a href='{parts[2].split('](')[1].split(')')[0]}' target='_blank' style='color:#10B981;'>Launch 🌐</a></td></tr>"

    index_layout = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>TrendForge Lab</title></head>
<body style="background:#0B0F19; color:#fff; font-family:sans-serif; text-align:center;">
    <h1>TrendForge Venture Lab</h1>
    <table style="margin:auto; width:80%; border-collapse:collapse;">
        <thead><tr><th>Date</th><th>Concept</th><th>Action</th></tr></thead>
        <tbody>{html_table_rows}</tbody>
    </table>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(index_layout)

def main():
    current_date = datetime.now().strftime("%Y-%m-%d")
    clients = get_api_clients()
    scout_data = call_trend_scout(clients)
    functional_code = call_core_developer(clients, scout_data)
    
    prod_name = "Autonomous Tool"
    for line in scout_data.split("\n"):
        if "PRODUCT NAME:" in line: prod_name = line.replace("PRODUCT NAME:", "").strip()
    
    clean_folder_name = "".join(c for c in prod_name if c.isalnum() or c in (' ', '_', '-')).rstrip().lower().replace(" ", "-")
    os.makedirs(f"products/{clean_folder_name}", exist_ok=True)
    with open(f"products/{clean_folder_name}/index.html", "w", encoding="utf-8") as f: f.write(functional_code)
            
    live_app_link = f"https://atharvahd6.github.io/trendforge-ai/products/{clean_folder_name}/"
    journal_entry = f"| {current_date} | **{prod_name}** | [Open Tool]({live_app_link}) |\n"
    
    # Idempotent Ledger Append
    if not os.path.exists("MASTER_TREND_JOURNAL.md"):
        with open("MASTER_TREND_JOURNAL.md", "w", encoding="utf-8") as f: f.write("# 📚 Master Autonomous Trend Journal\n\n| Date Run | Discovered Startup Concept | Live Web App Link |\n| :--- | :--- | :--- |\n")
    
    with open("MASTER_TREND_JOURNAL.md", "r+", encoding="utf-8") as f:
        content = f.read()
        if prod_name not in content: f.write(journal_entry)
            
    update_root_index()
    print("🏁 Operational cycle complete!")

if __name__ == "__main__": main()
