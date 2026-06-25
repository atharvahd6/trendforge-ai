# 🚀 TrendForge-AI (Venture Lab)

TrendForge-AI is an autonomous micro-SaaS incubator. Every day, the system wakes up, scans the digital landscape for market gaps (or uses an idea you've fed it manually), builds a coded MVP, deploys it as a live GitHub Pages app, and updates the ledger on the homepage automatically.

---

## 🎯 Why We Are Doing This (The Core Philosophy)

The biggest mistake founders make is wasting months building software before validating market demand. TrendForge-AI flips the script:

1. **Outcome First:** AI research and coding steps turn raw market signals into a concrete, production-ready single-page tool.
2. **Pre-Sell Validation (Smoke-Testing):** Each generated product is a real, deployable, live-linked tool — publish it and see if anyone bites before investing further engineering time.
3. **Infinite Historical Memory:** Every run creates a new folder under `products/`, gets its own live GitHub Pages URL, and is permanently logged in `MASTER_TREND_JOURNAL.md`. The homepage (`index.html`) is regenerated from that journal on every run, so it never drifts out of sync.

---

## 🤖 The Pipeline

Three stages run in sequence, each backed by a real AI provider call (no agent framework — direct calls to each provider's SDK, since `requirements.txt` only ships `google-genai`, `groq`, and `mistralai`):

| Stage | Job | Provider |
| --- | --- | --- |
| **1. Research** | Finds one concrete product opportunity — either from your `manual_ideas.txt` input or from autonomous trend-scanning. | Gemini (primary), Groq or Mistral (fallback) |
| **2. Build** | Converts the brief into a dark-themed, responsive single-page HTML/CSS/JS tool with localStorage persistence and a lead-capture modal. | Groq |
| **3. Audit** | Cleans up the HTML, fixes broken tags, adds basic error handling, strips any stray markdown code fences. | Mistral |

To stay resilient against rate limits, the **research** stage retries with a different provider if the first fails (see `FALLBACK_STRATEGIES` in `agent.py`). If all three fail, the run exits with an error so you can check API key status.

---

## 📂 The Permanent Repository Structure

```
📁 trendforge-ai/
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 run_agent.yml             # Daily cron trigger + manual dispatch + auto-commit
│
├── 📁 products/                         # 📂 Every generated product gets its own folder
│   ├── 📁 texttidy/
│   │   └── 📄 index.html
│   └── 📁 parking-spot-finder/
│       └── 📄 index.html
│
├── 📄 agent.py                          # Core pipeline (reads manual_ideas.txt, writes products/, updates journal + index.html)
├── 📄 MASTER_TREND_JOURNAL.md           # Source-of-truth dated table of every concept ever produced
├── 📄 manual_ideas.txt                  # Your manual override file — see below
├── 📄 index.html                        # Homepage dashboard — auto-regenerated from the journal every run
├── 📄 requirements.txt                  # google-genai, groq, mistralai
└── 📄 README.md                         # This file
```

Each product folder is served directly by GitHub Pages at:
`https://atharvahd6.github.io/trendforge-ai/products/<slug>/`

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

Commit and push the change (or edit it directly in the GitHub web UI).

### Step 2: The agent checks this file automatically

`agent.py` reads `manual_ideas.txt` at the start of every run, before anything else:

- **If it contains a filled-in idea:** the research stage skips trend-scanning entirely and builds your concept instead, end to end.
- **If it's empty or still just the blank template:** the engine runs in fully autonomous mode and scouts for a trend on its own.

### Step 3: Auto-cleanup happens for you

Once your manual idea has been processed and saved into `products/`, `agent.py` automatically blanks `manual_ideas.txt` back to the empty template — no manual cleanup step needed.

---

## 🗂️ How the Journal and Homepage Stay in Sync

Each run:
1. Computes a slug from the product's title (e.g. `parking-spot-finder`).
2. Writes the product to `products/<slug>/index.html`.
3. Appends a row to `MASTER_TREND_JOURNAL.md`.
4. **Regenerates `index.html` from the journal** — the homepage table is never hand-edited; it's always rebuilt from the journal's rows, so what you see on the live ledger always matches what's actually deployed.

If you ever need to hand-fix a journal entry, just edit `MASTER_TREND_JOURNAL.md` directly and run `agent.py`'s `rebuild_index_html()` step (or just wait for the next scheduled run) to regenerate the homepage from it.

---

## ⚡ Quick Deployment Verification

To keep this platform running for free, make sure your repository has these secrets configured under **Settings ➡️ Secrets and variables ➡️ Actions**:

- `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`

Also confirm **Workflow Permissions** are set to **Read and write permissions** under the Actions tab (Settings ➡️ Actions ➡️ General) — `run_agent.yml` needs write access to commit new product folders, the journal, and the regenerated homepage back to the repo.

Make sure **GitHub Pages** is enabled (Settings ➡️ Pages ➡️ deploy from the `main` branch) so each new `products/<slug>/` folder becomes a live URL automatically.
