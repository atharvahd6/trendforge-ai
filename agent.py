import os
import sys
from datetime import datetime
import google.generativeai as genai
from openai import OpenAI

def get_api_clients():
    clients = {}
    if os.environ.get("GEMINI_API_KEY"):
        try:
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            clients["gemini"] = True
        except: pass

    if os.environ.get("GROQ_API_KEY"):
        try:
            clients["groq"] = OpenAI(
                api_key=os.environ.get("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
        except: pass

    if os.environ.get("GITHUB_TOKEN"):
        try:
            clients["github"] = OpenAI(
                api_key=os.environ.get("GITHUB_TOKEN"),
                base_url="https://models.inference.ai.azure.com"
            )
        except: pass
    return clients

def call_trend_scout(clients):
    scout_prompt = (
        "Identify one hyper-specific digital product idea that solves a frustrating problem "
        "for average online users right now. Output EXACTLY in this format:\n"
        "PRODUCT NAME: [Name it]\n"
        "THE LIVE TREND/PROBLEM: [1 sentence explanation]\n"
        "WHAT IT DOES: [1-2 sentences clear value proposal]\n"
        "TARGET AUDIENCE: [Who will pay for this]"
    )
    if "gemini" in clients:
        try:
            print("🟢 Trend Scout: Trying Google Gemini...")
            model = genai.GenerativeModel("gemini-2.5-flash")
            return model.generate_content(scout_prompt).text.strip()
        except Exception as e:
            print(f"⚠️ Gemini failed or expired! Error: {e}")

    if "github" in clients:
        try:
            print("🟡 Fallback Triggered: Trying GitHub GPT-4o-Mini...")
            response = clients["github"].chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": scout_prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ GitHub fallback failed! Error: {e}")

    if "groq" in clients:
        try:
            print("🟡 Fallback Triggered: Trying Groq Llama...")
            response = clients["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": scout_prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Groq fallback failed! Error: {e}")

    raise Exception("🚨 Red Alert: All free AI providers have failed or expired simultaneously.")

def call_copy_critic(clients, marketer_output):
    critic_prompt = f"Review the Marketer's pitch. Refine it into cold, clear landing page text:\n\n{marketer_output}"
    if "github" in clients:
        try:
            print("🟢 Critic: Trying GitHub GPT-4o...")
            response = clients["github"].chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strict Direct-Response Copywriting Critic."},
                    {"role": "user", "content": critic_prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ GitHub Critic failed! Error: {e}")

    if "gemini" in clients:
        try:
            print("🟡 Fallback Critic: Trying Gemini...")
            model = genai.GenerativeModel("gemini-2.5-flash")
            return model.generate_content(critic_prompt).text.strip()
        except Exception as e:
            print(f"⚠️ Gemini Critic fallback failed! Error: {e}")

    return "Marketing optimization completed."

def main():
    current_date = datetime.now().strftime("%Y-%m-%d")
    clients = get_api_clients()
    
    try:
        scout_output = call_trend_scout(clients)
        
        print("🔥 Phase 2: Running Growth Marketer...")
        if "groq" in clients:
            try:
                res = clients["groq"].chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Optimize this startup concept:\n{scout_output}"}]
                )
                marketer_output = res.choices[0].message.content.strip()
            except:
                marketer_output = scout_output
        else:
            marketer_output = scout_output

        critic_output = call_copy_critic(clients, marketer_output)
        
        os.makedirs("archived_trends", exist_ok=True)
        dated_file_path = f"archived_trends/trend_{current_date}.md"
        
        final_report = (
            f"# 🚀 Startup Launch Kit - Deployed on {current_date}\n\n"
            f"### 💡 Core Concept Discovered:\n{scout_output}\n\n"
            f"### ⚡ Strategic Critique & Copy Elements:\n{critic_output}"
        )
        
        with open(dated_file_path, "w", encoding="utf-8") as f:
            f.write(final_report)
            
        prod_name = "Automated Micro-SaaS"
        for line in scout_output.split("\n"):
            if "PRODUCT NAME:" in line:
                prod_name = line.replace("PRODUCT NAME:", "").strip()

        journal_entry = f"| {current_date} | **{prod_name}** | [View Full Launch Kit 📂]({dated_file_path}) |\n"
        
        if not os.path.exists("MASTER_TREND_JOURNAL.md"):
            with open("MASTER_TREND_JOURNAL.md", "w", encoding="utf-8") as f:
                f.write("# 📚 Master Autonomous Trend Journal\n\n| Date Run | Discovered Startup Concept | Deep-Dive Link |\n| :--- | :--- | :--- |\n")
                
        with open("MASTER_TREND_JOURNAL.md", "a", encoding="utf-8") as f:
            f.write(journal_entry)
            
        print("🏁 Pipeline finished completely and safely!")
        
    except Exception as final_error:
        print(f"❌ Automation stopped: {final_error}")

if __name__ == "__main__":
    main()
