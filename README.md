# 🚀 TrendForge-AI (Hexa-Agent Venture Lab)

TrendForge-AI is an autonomous micro-SaaS incubator that runs 100% free using decentralized cloud networks and a collaborative matrix of 6 AI models. Every 24 hours, the system wakes up, scans the digital landscape for burning market gaps, profiles the target customer, maps out a technical code architecture, and designs a high-converting copywriting copy deck.

---

## 🎯 Why We Are Doing This (The Core Philosophy)

The biggest mistake founders make is wasting months building software before validating market demand. TrendForge-AI completely flips the script:

1. **Outcome First:** We use hyper-specialized AI personas to generate concrete, production-ready product concepts and marketing strategies out of raw internet trends.
2. **Pre-Sell Validation (Smoke-Testing):** Instead of wasting money building tools upfront, we publish these daily blueprints openly. If users show extreme interest or upgrade to a premium tier for custom, deep-dive reports, we gain **100% data-driven market confidence** before writing a single line of production code.
3. **Infinite Historical Memory:** Unlike generic AI setups that overwrite old ideas, this system creates automated time-stamped files inside a permanent archive folder. Your project history builds a compounding asset portfolio of side-hustle concepts that prospects can browse over time.

---

## 🤖 The Boardroom Agent Matrix

To make our execution bulletproof against API trial expirations or sudden model rate limits, we use a custom **Self-Healing Fallback Architecture**. If a top-tier provider hits a limit, the next available free model instantly saves the process.

| Agent Persona | Lead Model | Structural Backups | Commercial Role |
| --- | --- | --- | --- |
| **1. The Trend Scout** | Gemini 2.5 Flash | OpenAI GPT-4o / GitHub Mini | Mines real-time market pain points and defines the initial product value proposition. |
| **2. The Growth Marketer** | Groq Llama 3.3 (70B) | OpenAI GPT-4o | Designs aggressive direct-response hooks, angles, and viral launch strategies. |
| **3. The Audience Segmenter** | Cohere Command-R+ | System Bypasses Safely | Standardizes demographic targets, identifying customer budget limits and motivations. |
| **4. The Code Architect** | Mistral Large | GitHub Models Native | Formulates a 3-step rapid MVP codebase structure and screens for regional data risks. |
| **5. The Copywriting Critic** | GitHub Models GPT-4o | Gemini / Default Rails | Wields direct psychology to cut through corporate fluff and render final high-converting copy. |

---

## 📂 The Permanent Repository Structure

```text
📁 trendforge-ai/
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 run_agent.yml             # The Daily Automation Trigger & Git Committer
│
├── 📁 archived_trends/                 # 📂 Where every daily startup concept is stored forever
│   ├── 📄 trend_2026-05-26.md          # Example: Individual daily launch kit file
│   └── 📄 trend_2026-05-27.md          # Example: Next operational cycle's output file
│
├── 📄 agent.py                          # The core Multi-AI integration and execution script
├── 📄 MASTER_TREND_JOURNAL.md          # The central database timeline showing all historical ideas
├── 📄 manual_ideas.txt                  # 🆕 Your personal control file to manually feed custom ideas
└── 📄 README.md                         # This master documentation dashboard

```

---

## 💡 How to Add and Run Your Own Ideas Manually

While the system is engineered to run fully autonomously on its daily clock, **you have complete manual override power.** If you wake up with a brilliant business idea that you want your 6-agent boardroom to analyze, structure, and write copy for, follow this step-by-step process:

### Step 1: Populate the Control File

Create a file named **`manual_ideas.txt`** directly in the root of your GitHub repository. Inside that file, type your concept cleanly. For example:

```text
PRODUCT NAME: RealEstate-Khatha-Bot
WHAT IT DOES: An automation script that tracks municipal property documentation and automatically flags application errors on local government portals.
TARGET AUDIENCE: Property owners and property management firms in Karnataka.

```

### Step 2: The Code is Already Prepared to Listen

The `agent.py` file is strategically coded to check this file first.

* **If `manual_ideas.txt` contains text:** The Trend Scout agent will freeze its web-scraping loop, lock onto your custom idea, and pass your concept to the Marketer, Profiler, Architect, and Critic.
* **If `manual_ideas.txt` is completely empty or deleted:** The engine resumes its fully autonomous mode, scouting the live internet for trends on its own.

### Step 3: Clean up for the Next Run

Once the system finishes processing your custom concept and saves your launch kit inside the `archived_trends/` folder, simply open `manual_ideas.txt` on GitHub, delete the text inside to make it blank again, and hit commit. The system will cleanly slide back into 100% autonomous trend-hunting for the next morning!

---

## ⚡ Quick Deployment Verification

To keep this entire platform completely free forever, verify that your repository backend is armed with your 5 secure tokens under **Settings ➡️ Secrets and variables ➡️ Actions**:

* `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `COHERE_API_KEY`, and `MISTRAL_API_KEY`.

Ensure **Workflow Permissions** are set to **Read and write permissions** under the Actions tab so your agents can write directly to your database history!
