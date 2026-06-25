# 🚀 TrendForge-AI (Hexa-Agent Venture Lab)

TrendForge-AI is an autonomous micro-SaaS incubator. Every day, the system wakes up, scans the digital landscape for market gaps (or uses an idea you've fed it manually), maps out a coded MVP, and saves a deployable single-file HTML product into a permanent archive.

---

## 🎯 Why We Are Doing This (The Core Philosophy)

The biggest mistake founders make is wasting months building software before validating market demand. TrendForge-AI flips the script:

1. **Outcome First:** Hyper-specialized AI personas turn raw market signals into concrete, production-ready product concepts.
2. **Pre-Sell Validation (Smoke-Testing):** Each generated product is a real, deployable single-page tool — publish it and see if anyone bites before investing further engineering time.
3. **Infinite Historical Memory:** Every run writes a new, uniquely-named file into `products/` and appends an entry to `MASTER_TREND_JOURNAL.md`. Nothing gets overwritten — the archive compounds over time.

---

## 🤖 The Boardroom Agent Matrix

To stay resilient against API trial expirations or rate limits, the pipeline uses a **Self-Healing Fallback Architecture**. If a provider hits a limit, the next strategy in the list takes over automatically.

| Agent Persona | Lead Model | Structural Backups | Commercial Role |
| --- | --- | --- | --- |
| **1. Trend/Research Analyst** | Gemini 2.0 Flash | Groq Llama 3.3 / Mistral Large | Finds one concrete, high-potential product opportunity — either from your `manual_ideas.txt` input or from autonomous trend-scanning. |
| **2. UI Architect** | Groq Llama 3.3 (70B) | — | Converts the concept into a dark-themed, responsive single-page HTML/CSS/JS tool with localStorage persistence. |
| **3. Compliance Auditor** | Mistral Large | — | Merges everything into one clean, deployable HTML file and writes it to `products/`. |

Each daily run tries strategies in order until one succeeds; if all three fail, the run exits with an error so you can check API key status.

---

## 📂 The Permanent Repository Structure

```
📁 trendforge-ai/
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 run_agent.yml             # Daily cron trigger + manual dispatch + auto-commit
│
├── 📁 products/                         # 📂 Every generated product lives here, one file per run
│   ├── 📄 some-concept-slug-2026-06-24.html
│   └── 📄 another-concept-slug-2026-06-25.html
│
├── 📄 agent.py                          # Core multi-agent pipeline (reads manual_ideas.txt, writes products/, updates journal)
├── 📄 MASTER_TREND_JOURNAL.md           # Auto-appended dated index of every concept ever produced
├── 📄 manual_ideas.txt                  # Your manual override file — see below
└── 📄 README.md                         # This file
```

---

## 💡 How to Add and Run Your Own Ideas Manually

The system runs autonomously on its daily schedule, but you can override it any time:

### Step 1: Fill in `manual_ideas.txt`

Open `manual_ideas.txt` at the repo root and fill in the template:

```
PRODUCT NAME: RealEstate-Khatha-Bot
WHAT IT DOES: An automation script that tracks municipal property documentation and flags application errors on local government portals.
TARGET AUDIENCE: Property owners and property management firms in Karnataka.
```

Commit and push the change (or just edit it directly in the GitHub web UI).

### Step 2: The agent checks this file automatically

`agent.py` reads `manual_ideas.txt` at the start of every run, before doing anything else:

- **If it contains a filled-in idea:** the research agent skips trend-scanning entirely and builds your concept instead, end to end.
- **If it's empty or still just the blank template:** the engine runs in fully autonomous mode and scouts for a trend on its own.

### Step 3: Auto-cleanup happens for you

Once your manual idea has been processed and saved into `products/`, `agent.py` automatically blanks `manual_ideas.txt` back to the empty template — no manual cleanup step needed. The very next scheduled run will go back to autonomous scouting unless you fill the file in again first.

---

## 🗂️ How Output Files Are Named

Each run computes a filename from the product's title plus the run date, e.g. `products/parking-finder-app-2026-06-25.html`. This means:

- Nothing is ever overwritten — every run adds a new file.
- `MASTER_TREND_JOURNAL.md` gets a matching dated entry linking to the file, so the journal stays in sync with what's actually in `products/`.

---

## ⚡ Quick Deployment Verification

To keep this platform running for free, make sure your repository has these secrets configured under **Settings ➡️ Secrets and variables ➡️ Actions**:

- `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `COHERE_API_KEY`, and `MISTRAL_API_KEY`

Also confirm **Workflow Permissions** are set to **Read and write permissions** under the Actions tab (Settings ➡️ Actions ➡️ General) — `run_agent.yml` needs write access to commit new product files and journal updates back to the repo.
