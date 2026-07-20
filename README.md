# TrendForge Venture Lab

**An autonomous agent that ships one complete, deployed micro-SaaS tool every 24 hours.**

Every run: research a niche problem → write the product brief → generate a working single-page
HTML/CSS/JS tool → audit and clean it up → deploy it to GitHub Pages → log it in the public ledger.
No human in the loop unless you drop an idea into `manual_ideas.txt`.

Live ledger: **[Launch the dashboard](https://atharvahd6.github.io/trendforge-ai/)**

---

## Quick Start

### Prerequisites

- Python 3.10+
- At least one of: `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`
- `requirements.txt` → `google-genai`, `groq`, `mistralai`

### Run it

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...      # optional
export GROQ_API_KEY=...        # optional
export MISTRAL_API_KEY=...     # optional, but recommended (see note below)
python agent.py
```

> **Note on keys:** the pipeline only *requires* one key to start, but the audit stage prefers
> Mistral as a fixed, independent auditor. If `MISTRAL_API_KEY` isn't set, audit now falls back
> to the strategy's own coding provider instead of failing the whole run — see
> `resolve_audit_provider()` in `agent.py` and the "Known Issues (Fixed)" section below.

### Give it a specific idea instead of autonomous scouting

Drop a brief into `manual_ideas.txt`:

```
PRODUCT NAME: Invoice Reminder Scheduler
Target audience: freelance designers
Core problem: chasing late client payments manually
```

The next run consumes it, clears the file, and resumes autonomous scouting afterward.

---

## How It Works

```
main()
  │
  ▼
FALLBACK_STRATEGIES loop (Gemini+Groq → Pure Groq → Mistral+Groq)
  │
  ▼
run_agent_pipeline(strategy)
  │
  ├─ 1. IDEA        manual_ideas.txt present? → use it (and clear it after)
  │                 else → research_provider proposes a NEW idea, explicitly
  │                 banned from repeating the last 15 shipped titles
  │
  ├─ 2. RESEARCH     research_provider → markdown brief
  │                  (# Product Name / audience / problem / value prop)
  │
  ├─ 3. CODE         coding_provider → single-file HTML/CSS/JS tool
  │                  (localStorage persistence + lead-capture modal
  │                  posting to salarybit.in/api/v1/lead-intake)
  │
  ├─ 4. AUDIT        resolve_audit_provider(strategy) → cleans up the HTML,
  │                  fixes broken tags, adds error handling
  │
  ├─ 5. DEPLOY       writes products/<date>-<slug>/index.html
  │                  (date-prefixed — prevents same-day slug collisions
  │                  from overwriting a previous day's live tool)
  │
  └─ 6. LOG          appends a row to MASTER_TREND_JOURNAL.md,
                     regenerates index.html from the full journal
```

If a strategy throws, the executor loop waits 5s and retries with the next fallback
strategy. Only exits non-zero if all three are exhausted.

---

## Architecture

```
trendforge-ai/
├── agent.py                   # the whole pipeline — single file, no framework
├── manual_ideas.txt            # optional human override, blanked after use
├── MASTER_TREND_JOURNAL.md     # append-only ledger: date | concept | link
├── index.html                  # regenerated every run from the journal
├── products/
│   └── YYYY-MM-DD-<slug>/
│       └── index.html          # the deployed, standalone tool for that day
├── requirements.txt             # google-genai, groq, mistralai
├── AGENT_GUIDE.md               # operating contract for an agent picking this up cold
└── PROJECT_CONTEXT.md           # architecture reference / design decisions log
```

**Why one file (`agent.py`)?** No agent framework — every provider is called directly
against its own SDK (`google-genai`, `groq`, `mistralai`), so there's nothing else to install
or configure to run the pipeline end to end.

---

## Known Issues (Fixed in this pass)

- **Audit stage hardcoded to Mistral regardless of configured keys.** Previously
  `run_agent_pipeline()` always called `call_provider("mistral", audit_prompt)`, but the
  startup check only requires *any one* of the three API keys. A deployment running with
  only `GEMINI_API_KEY` + `GROQ_API_KEY` set would pass the startup check, then fail at the
  audit step on **every** fallback strategy (all three route audit through Mistral) —
  producing a `CRITICAL SYSTEM FAILURE` even though two working providers were configured.
  Fixed with `resolve_audit_provider(strategy)`: prefers Mistral when available, otherwise
  falls back to that strategy's own `coding_provider`.
- **Slug collisions** (pre-existing bugfix, already in the code you uploaded): folder names
  are now date-prefixed (`products/YYYY-MM-DD-<slug>/`) so two different ideas that trim down
  to the same 6-word slug no longer overwrite each other's live URL.
- **Idea repetition** (pre-existing bugfix, already in the code you uploaded): the research
  prompt now includes the last 15 shipped titles with an explicit "do not repeat or submit a
  close variant" instruction, so the scout stops converging on the same comfortable idea
  (this is why the journal shows nine near-identical "Content Calendar for X" entries before
  2026-07-12, and genuinely distinct concepts after).

---

## Contributing

- **New provider:** add a `call_<provider>()` wrapper + register it in `PROVIDER_CALLERS`.
- **New fallback ordering:** edit `FALLBACK_STRATEGIES`.
- **Change the deployed tool's shape:** edit the `coding_prompt` template in
  `run_agent_pipeline()` — e.g. to always include a specific analytics snippet or footer.
