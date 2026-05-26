import os
import sys
import time
from datetime import datetime
from google import genai
from openai import OpenAI
import cohere
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

# --- PHASE 1-3: LOGIC SAME AS PREVIOUS ---
# [Assume call_trend_scout, call_core_developer, call_personal_marketer are included here]

# --- PHASE 4: THE MASTER LEDGER UPDATER ---
def update_root_index():
    if not os.path.exists("MASTER_TREND_JOURNAL.md"): return
    with open("MASTER_TREND_JOURNAL.md", "r", encoding="utf-8") as f: lines = f.readlines()
        
    html_table_rows = ""
    for line in lines:
        clean_line = line.strip()
        if not clean_line.startswith("|") or "Date Run" in clean_line or ":---" in clean_line: continue
        parts = [p.strip() for p in clean_line.split("|")[1:-1]]
        if len(parts) >= 3:
            html_table_rows += f"""
            <tr>
                <td>{parts[0]}</td>
                <td style="font-weight:600; color:#fff;">{parts[1].replace("**", "")}</td>
                <td><a href="{parts[2].split("](")[1].split(")")[0]}" target="_blank" style="color:#10B981; text-decoration:none; font-weight:bold;">Launch 🌐</a></td>
            </tr>"""

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
    target_dir = f"products/{clean_folder_name}"
    os.makedirs(target_dir, exist_ok=True)
    with open(f"{target_dir}/index.html", "w", encoding="utf-8") as f: f.write(functional_code)
            
    live_app_link = f"https://atharvahd6.github.io/trendforge-ai/products/{clean_folder_name}/"
    journal_entry = f"| {current_date} | **{prod_name}** | [Open Tool]({live_app_link}) |\n"
    
    # IDEMPOTENT APPEND
    with open("MASTER_TREND_JOURNAL.md", "r+", encoding="utf-8") as f:
        content = f.read()
        if prod_name not in content:
            f.write(journal_entry)
            
    update_root_index()
    print("🏁 Operational cycle complete!")

if __name__ == "__main__": main()
