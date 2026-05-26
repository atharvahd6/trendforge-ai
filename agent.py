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
    
    # 1. OpenAI ChatGPT Client
    if os.environ.get("OPENAI_API_KEY"):
        try: clients["openai"] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except: print("⚠️ OpenAI client setup failed.")

    # 2. Modern Google GenAI Client
    if os.environ.get("GEMINI_API_KEY"):
        try:
            # Picks up GEMINI_API_KEY from environment variables automatically
            clients["gemini"] = genai.Client()
        except Exception as e: print(f"⚠️ Gemini configuration failed: {e}")

    # 3. Groq Client (Llama 3.3)
    if os.environ.get("GROQ_API_KEY"):
        try:
            clients["groq"] = OpenAI(
                api_key=os.environ.get("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
        except: print("⚠️ Groq client setup failed.")

    # 4. Cohere Client
    if os.environ.get("COHERE_API_KEY"):
        try: clients["cohere"] = cohere.ClientV2(api_key=os.environ.get("COHERE_API_KEY"))
        except: print("⚠️ Cohere client setup failed.")

    # 5. Mistral AI Client (Updated routing location)
    if os.environ.get("MISTRAL_API_KEY"):
        try: clients["mistral"] = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
        except Exception as e: print(f"⚠️ Mistral client setup failed: {e}")

    # 6. GitHub Models (Copilot Native Token Fallback)
    if os.environ.get("GITHUB_TOKEN"):
        try:
            clients["github"] = OpenAI(
                api_key=os.environ.get("GITHUB_TOKEN"),
                base_url="https://models.inference.ai.azure.com"
            )
        except: print("⚠️ GitHub Native Token client setup failed.")
        
    return clients

# --- PHASE 1: THE TREND SCOUT (Gemini / OpenAI Fallback) ---
def call_trend_scout(clients):
    scout_prompt = (
        "Identify one hyper-specific digital product or micro-SaaS idea that solves a painful problem "
        "for online users right now. Output EXACTLY in this format:\n"
        "PRODUCT NAME: [Name it]\n"
        "THE LIVE TREND/PROBLEM: [1 sentence explanation]\n"
        "WHAT IT DOES: [1-2 sentences clear value proposal]\n"
        "TARGET AUDIENCE: [Who will pay for this]"
    )
    
    # Check for manual ideas override file first
    if os.path.exists("manual_ideas.txt"):
        with open("manual_ideas.txt", "r", encoding="utf-8") as f:
            manual_content = f.read().strip()
        if manual_content:
            print("🎯 Custom Manual Override File Detected! Using your user defined concept...")
            return manual_content

    if "gemini" in clients:
        try:
            print("🟢 Role 1: Trend Scout running via Google Gemini...")
            response = clients["gemini"].models.generate_content(
                model="gemini-2.5-flash",
                contents=scout_prompt,
            )
            return response.text.strip()
        except Exception as e: 
            print(f"⚠️ Gemini execution failed: {e}. Moving to fallback...")

    if "openai" in clients:
        try:
            print("🟡 Trend Scout Fallback: Running via OpenAI GPT-4o...")
            res = clients["openai"].chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": scout_prompt}]
            )
            return res.choices[0].message.content.strip()
        except: pass

    if "github" in clients:
        print("🔵 Trend Scout Hard Fallback: Running via Free GitHub Engine...")
        res = clients["github"].chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": scout_prompt}]
        )
        return res.choices[0].message.content.strip()
    
    raise Exception("No active keys available for Phase 1 Scouting.")

# --- PHASE 2: THE GROWTH MARKETER (Groq Llama-70B / OpenAI Fallback) ---
def call_growth_marketer(clients, scout_output):
    prompt = f"Analyze this product and generate 3 aggressive direct-response hooks:\n\n{scout_output}"
    if "groq" in clients:
        try:
            print("🟢 Role 2: Growth Marketer processing via Groq Llama 3.3...")
            res = clients["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content.strip()
        except: pass
        
    if "openai" in clients:
        try:
            print("🟡 Growth Marketer Fallback: Running via OpenAI GPT-4o...")
            res = clients["openai"].chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content.strip()
        except: pass

    return "Marketer Agent offline due to key restrictions. Bypassing strategy framework step safely."

# --- PHASE 3: AUDIENCE DEMOGRAPHICS TARGETER (Cohere / ChatGPT Fallback) ---
def call_audience_segmenter(clients, scout_output):
    prompt = f"Based on this concept, define the core user persona, their psychological pain point, and their wallet budget size:\n\n{scout_output}"
    if "cohere" in clients:
        try:
            print("🟢 Role 3: Audience Profiler running via Cohere...")
            res = clients["cohere"].chat(model="command-r-plus", messages=[{"role": "user", "content": prompt}])
            return res.message.content[0].text.strip()
        except: pass

    return "Audience segmentation skipped safely."

# --- PHASE 4: CODE ARCHITECT & RISK ANALYST (Mistral / Free GitHub Fallback) ---
def call_technical_analyst(clients, scout_output):
    prompt = f"Review this tech stack requirement. Provide a clean, rapid 3-step MVP development layout and note any privacy hurdles:\n\n{scout_output}"
    if "mistral" in clients:
        try:
            print("🟢 Role 4: Code Architect mapping layouts via Mistral...")
            res = clients["mistral"].chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
            return res.choices[0].message.content.strip()
        except: pass

    return "Technical feasibility checks bypassed safely."

# --- PHASE 5: THE STRATEGIC COPY CRITIC (GitHub Copilot GPT-4o Always Free) ---
def call_copy_critic(clients, market_data):
    prompt = f"Review this collective agency notes block. Strip all corporate hype. Output a sharp, high-converting launch copy deck:\n\n{market_data}"
    if "github" in clients:
        try:
            print("🟢 Role 5: Copy Critic executing audit via GitHub Models GPT-4o...")
            res = clients["github"].chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strict Copywriting Critic."},
                    {"role": "user", "content": prompt}
                ]
            )
            return res.choices[0].message.content.strip()
        except: pass
        
    return "Launch copy structure updated."

# --- CORE INTEGRATION ENGINE ---
def main():
    current_date = datetime.now().strftime("%Y-%m-%d")
    clients = get_api_clients()
    
    try:
        # Run the full pipeline chain
        scout_data = call_trend_scout(clients)
        marketing_data = call_growth_marketer(clients, scout_data)
        audience_data = call_audience_segmenter(clients, scout_data)
        tech_data = call_technical_analyst(clients, scout_data)
        
        compiled_brief = f"{marketing_data}\n\n## 👥 User Segmentation\n{audience_data}\n\n## 🛠️ Technical Plan\n{tech_data}"
        final_copy_kit = call_copy_critic(clients, compiled_brief)
        
        # Save to permanent dated folder archive
        os.makedirs("archived_trends", exist_ok=True)
        dated_file_path = f"archived_trends/trend_{current_date}.md"
        
        final_report = (
            f"# 🚀 Automated Startup Launch Kit ({current_date})\n\n"
            f"## 💡 Micro-SaaS Business Concept\n{scout_data}\n\n"
            f"## 🎯 Conversion Copywriting & Go-To-Market Execution Package\n{final_copy_kit}"
        )
        
        with open(dated_file_path, "w", encoding="utf-8") as f:
            f.write(final_report)
            
        # Parse product line name safely for index table
        prod_name = "Automated Micro-SaaS"
        for line in scout_data.split("\n"):
            if "PRODUCT NAME:" in line:
                prod_name = line.replace("PRODUCT NAME:", "").strip()

        # Update running chronological timeline record index
        journal_entry = f"| {current_date} | **{prod_name}** | [View Full Launch Kit 📂]({dated_file_path}) |\n"
        
        if not os.path.exists("MASTER_TREND_JOURNAL.md"):
            with open("MASTER_TREND_JOURNAL.md", "w", encoding="utf-8") as f:
                f.write("# 📚 Master Autonomous Trend Journal\n\n| Date Run | Discovered Startup Concept | Deep-Dive Link |\n| :--- | :--- | :--- |\n")
                
        with open("MASTER_TREND_JOURNAL.md", "a", encoding="utf-8") as f:
            f.write(journal_entry)
            
        print("🏁 Operational cycle complete! Historical links safely pushed.")
        
    except Exception as final_error:
        print(f"❌ Operation terminated prematurely: {final_error}")

if __name__ == "__main__":
    main()
