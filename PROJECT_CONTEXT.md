# Project Context — TrendForge Venture Lab

Architecture reference and the history of *why* the code looks the way it does.
If you're about to "simplify" something here, check whether it's actually a scar
from a bug that already happened once — see the BUGFIX comments in `agent.py`.

## Design goals

1. **Zero human intervention by default.** The agent proposes its own idea every run unless
   `manual_ideas.txt` has real content in it.
2. **One deployed artifact per run, permanently addressable.** Every run's output must live at
   its own stable URL forever — later runs must never overwrite an earlier one.
3. **No framework, direct SDK calls.** Kept deliberately simple: `requirements.txt` only ships
   `google-genai`, `groq`, `mistralai`. Anyone reading `agent.py` top to bottom can see the
   entire system.
4. **Fail over, don't fail hard.** Three fallback strategies (`FALLBACK_STRATEGIES`) trade
   which provider does research vs. coding, so a single provider outage doesn't stop the
   day's run.

## Pipeline stages and their single responsibility

| Stage | Function | Provider source |
|---|---|---|
| Idea | `read_manual_idea()` / research prompt | manual override, or `strategy["research_provider"]` |
| Research | inline prompt in `run_agent_pipeline()` | `strategy["research_provider"]` |
| Code | inline prompt in `run_agent_pipeline()` | `strategy["coding_provider"]` |
| Audit | inline prompt in `run_agent_pipeline()` | `resolve_audit_provider(strategy)` |
| Deploy | file write to `products/<slug>/index.html` | — |
| Log | `append_journal_row()` + `rebuild_index_html()` | — |

## Decision log

- **2026 (date of upload) — Audit provider hardcoding fixed.** `resolve_audit_provider()`
  introduced so audit degrades to the strategy's coding provider when `MISTRAL_API_KEY` is
  absent, instead of hard-failing every fallback strategy. Previously the startup check
  ("any one key is enough") was inconsistent with the audit stage's actual requirement
  ("Mistral, always") — this closes that gap without forcing Mistral to be mandatory.
- **Slug collisions → date-prefixed folders.** `slugify()` only keeps the first 6 words of a
  title, so two distinct ideas sharing an opening phrase (e.g. two "...Content Calendar for
  X" briefs) used to collapse to the identical folder name, and `os.makedirs(..., exist_ok=True)`
  silently reused it — meaning the second run's deploy overwrote the first run's *live* URL.
  Fixed by prefixing every folder with the UTC run date, plus a numeric-suffix loop for the
  (rare) case of two runs landing on the same day.
- **Idea repetition → anti-repeat clause.** Without memory of prior runs, the research
  prompt kept converging on the same "safe" idea shape across many consecutive days (visible
  in the journal as ~9 near-identical "Content Calendar for &lt;audience&gt;" entries in a row).
  `get_recent_titles(limit=15)` now feeds the last 15 shipped titles back into the research
  prompt with an explicit instruction to avoid repeats and close variants.

## Open questions / not yet decided

- Whether `salarybit.in/api/v1/lead-intake` should get a shared JSON schema doc so every
  generated tool's lead-capture payload stays consistent as the coding prompt evolves.
- Whether `GEMINI_MODEL` / `GROQ_MODEL` / `MISTRAL_MODEL` should be overridable via env vars
  instead of hardcoded constants, now that model naming shifts every few months.
