import os
import re
import time
import json
import sqlite3
import hashlib
from datetime import datetime
from google import genai
from groq import Groq
try:
    from mistralai.client import Mistral
except ImportError:
    from mistralai import Mistral


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

SCOUT_MAX_RETRIES   = 3      # How many times Stage 1 can retry before giving up
AUDIT_DB_PATH       = "scout_audit.db"
PRODUCTS_DIR        = "products"
INPUT_IDEA_FILE     = "INPUT_IDEA.txt"

# Tracks providers that hit a quota/auth error this session — skip them instantly
_EXHAUSTED_PROVIDERS: set = set()


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOGGER
# ─────────────────────────────────────────────────────────────────────────────

def init_audit_db():
    """Creates the audit log SQLite database and table if they don't exist."""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            action      TEXT    NOT NULL,
            provider    TEXT,
            outcome     TEXT    NOT NULL,
            detail      TEXT
        )
    """)
    conn.commit()
    conn.close()


def audit(action: str, outcome: str, provider: str = None, detail: str = None):
    """Writes one record to the audit log. Never raises — failures are printed only."""
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.execute(
            "INSERT INTO audit_log (timestamp, action, provider, outcome, detail) VALUES (?,?,?,?,?)",
            (datetime.utcnow().isoformat(), action, provider, outcome, detail)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[AUDIT] Write failed (non-fatal): {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CLIENT INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def get_clients():
    """Initializes available AI clients safely."""
    return {
        "gemini":  genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))  if os.environ.get("GEMINI_API_KEY")  else None,
        "groq":    Groq(api_key=os.environ.get("GROQ_API_KEY"))            if os.environ.get("GROQ_API_KEY")    else None,
        "mistral": Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))      if os.environ.get("MISTRAL_API_KEY") else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TWO-STAGE SCOUT PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

def get_scout_validation_prompt() -> str:
    """
    Stage 1 — Idea Scouting + Gate Validation.

    The LLM scouts ONE enterprise tool idea and immediately stress-tests it
    against three hard business-viability gates. Only ideas that pass all
    three gates emit [GATE: PASS] and move to Stage 2.
    """
    return """
You are an elite Enterprise Software Architect and B2B SaaS Product Director
with 20 years of experience selling software to Fortune 500 companies in
regulated industries. You have a ruthless instinct for what a CISO, General
Counsel, or VP of Compliance will actually sign a purchase order for — versus
what sounds impressive but dies in procurement.

════════════════════════════════════════════════════════════
MISSION
════════════════════════════════════════════════════════════
Identify ONE specific, painful operational problem inside a massive corporation
in one of these five regulated verticals:
  • Financial Services (investment banking, insurance, asset management)
  • Healthcare (hospital networks, pharma, medical device manufacturers)
  • Legal (AmLaw 100 firms, in-house corporate legal departments)
  • Cybersecurity (MSSPs, SOC teams, threat intelligence units)
  • Defense / Government Contracting (prime contractors, cleared facilities)

The solution MUST be a 100% offline, air-gapped desktop application.
Zero cloud calls. Zero telemetry. Zero internet dependency of any kind.
It runs on a locked-down Windows or Linux workstation inside a corporate
intranet or SCIF. Data never leaves the machine.

════════════════════════════════════════════════════════════
HARD REJECTION LIST — Do NOT generate ideas in these categories
════════════════════════════════════════════════════════════
• Anything requiring a web request, REST call, or external API
• Basic log viewers that lack an AI summarization pipeline
• PDF readers without an extraction + structured analysis layer
• Tools solvable by a 50-line script or a free command-line utility
• Markdown editors, calculators, file renamers, or simple scrapers
• Anything a junior developer could prototype in under 2 hours
• Generic "chatbot wrapper" apps with no domain-specific processing logic
• Tools that duplicate what Notepad++, VS Code, or Excel already handle natively

════════════════════════════════════════════════════════════
GATE QUESTIONS — Answer ALL THREE internally before proceeding
════════════════════════════════════════════════════════════
Gate 1 — Executive Sponsorship:
  Would a CISO, General Counsel, or Chief Compliance Officer personally
  authorize a budget line item for this tool? Is this their problem, not
  an IT department afterthought?

Gate 2 — Manual Labour Elimination:
  Does this tool eliminate a workflow currently performed manually by a
  team of at least 3 full-time employees, paralegals, analysts, or
  junior associates? Is there a measurable FTE-hours saving?

Gate 3 — Competitor Displacement:
  Is there an existing SaaS product priced at $50,000+/year that
  enterprises refuse to buy because it requires cloud upload of sensitive
  data? Does this offline tool solve exactly that trust problem?

If ANY gate answer is NO, discard the idea and pick a different one.
Do not reveal rejected ideas. Only present the one that passed all three.

════════════════════════════════════════════════════════════
OUTPUT FORMAT — Respond strictly in this structure
════════════════════════════════════════════════════════════

GATE VERDICT: [PASS] or [FAIL — reason]
  (If FAIL, stop. Output only: [GATE: FAIL] — <one-line reason>)

PRODUCT NAME:
  [Professional, market-ready enterprise software name.
   Should sound like a vendor product, not a hackathon project.
   Good register: "AuditSentinel Pro", "LexVault Analyzer", "ClearanceDesk AI".]

INDUSTRY VERTICAL:
  [One of the five verticals listed above]

PROBLEM STATEMENT:
  [3–5 sentences. Name the job title suffering the problem, the regulatory
   framework creating the obligation (SOX, HIPAA, FedRAMP, GDPR, etc.),
   and the financial or legal consequence of the problem remaining unsolved.]

COMPETITOR GAP ANALYSIS:
  Competitor 1: [Real product name]
    What it does: [one sentence]
    Why enterprises reject it: [cloud dependency / pricing / missing feature]
  Competitor 2: [Real product name]
    What it does: [one sentence]
    Why enterprises reject it: [cloud dependency / pricing / missing feature]
  Our Displacement Angle: [Why offline + local AI wins where these two lose]

BUYER PROFILE:
  Primary Buyer Title: [e.g., VP of Compliance, Head of InfoSec]
  Company Type: [e.g., AmLaw 100 firm, Tier-1 investment bank]
  Team Suffering the Problem: [e.g., 6-person compliance analyst team]
  Estimated Manual Hours Saved Per Week: [conservative number]

USER STORY:
  [One vivid paragraph. Name a fictional but realistic employee — job title,
   company type, and a specific crisis moment (Friday 4pm before a regulatory
   audit, a breach triage at 2am, a merger due-diligence crunch). Describe
   the exact moment they discover this tool eliminates their crisis.]

MONETIZATION MODEL:
  Pricing Structure: [One-time license / Annual per-seat / Site license / Gov task order]
  Price Point: [e.g., $8,000–$15,000 one-time per workstation]
  Sales Motion: [Direct outreach / VAR/MSP / GSA schedule / Law firm tech consultant]
  Upsell Path: [What does v2.0 or an enterprise tier look like?]

[GATE: PASS]
"""


def get_scout_spec_prompt(validation_output: str) -> str:
    """
    Stage 2 — Full Technical Spec + Code Generation.

    Only called when Stage 1 returns [GATE: PASS].
    Produces a complete build specification and the full Python application.
    """
    return f"""
You are a senior Python architect who specialises in production-grade,
air-gapped enterprise desktop utilities using Tkinter and local Ollama endpoints.
You write clean, well-commented, maintainable code that a mid-level developer
can extend without your guidance.

════════════════════════════════════════════════════════════
CONTEXT — Validated Enterprise Product Idea
════════════════════════════════════════════════════════════
The following product idea has already passed a three-gate business viability
check. Do not re-evaluate the idea. Produce the full technical spec and code.

--- BEGIN VALIDATED IDEA ---
{validation_output}
--- END VALIDATED IDEA ---

════════════════════════════════════════════════════════════
MANDATORY TECHNICAL CONSTRAINTS
════════════════════════════════════════════════════════════
1. GUI Framework: Python Tkinter only. No PyQt, no Electron, no web UI.
   Must run with no GUI deps beyond tkinter (ships with CPython).

2. AI Integration: Local Ollama endpoint only (http://localhost:11434).
   - Model selection configurable (default: llama3 for reasoning,
     codellama for code audit, mistral for summarization).
   - All Ollama calls MUST:
       a) Strip PII before the text reaches subprocess (regex pre-filter).
          Redact: emails, IPs, credit cards, SSNs, API keys, JWTs,
          PEM private key headers, high-entropy base64 strings (>40 chars).
       b) Use Ollama's JSON mode where the model supports it.
       c) Include a configurable timeout (default 120s) with graceful fallback.
       d) Run in a background threading.Thread. Use queue.Queue to pass
          results back to the GUI thread. Never freeze the Tkinter main loop.
       e) Show a non-blocking animated progress indicator (ttk.Progressbar
          in indeterminate mode) during inference.

3. File Processing: Python native modules only (os, pathlib, re, json,
   csv, sqlite3, hashlib). No pandas or numpy unless strictly required.

4. Data Sovereignty: Zero network calls except the local Ollama subprocess.
   Add this comment block at the top of the generated file:
   # NETWORK POLICY: No external network calls.
   # Ollama subprocess is localhost-only.

5. Audit Logging: Every file processed, every AI call, and every export
   must be written to audit.db (SQLite, in the app directory) with:
   timestamp, action_type, file_hash (SHA-256), and outcome.

════════════════════════════════════════════════════════════
GUI LAYOUT REQUIREMENTS
════════════════════════════════════════════════════════════
Panel 1 — Input / File Loading Zone
  • Browse Files button + file queue listbox (⏳ pending / ✅ done / ❌ error)
  • Clear queue button

Panel 2 — Configuration Panel
  • Ollama model selector dropdown
  • PII redaction toggle (ON by default)
  • Output format selector (JSON / CSV / plain text)
  • Timeout slider (30s – 300s)

Panel 3 — Live Processing Log
  • Scrollable text widget, color-coded: INFO/WARNING/ERROR/SUCCESS
  • Timestamp on every log line

Panel 4 — Results / Output Viewer
  • Structured AI output display
  • Copy-to-clipboard + Export + Clear buttons

Status Bar: current operation | progress indicator | audit record count
Menu Bar: File | Settings | Audit | Help

════════════════════════════════════════════════════════════
FEATURE PIPELINE — Implement exactly 5 core features
════════════════════════════════════════════════════════════
For each feature output:
  FEATURE [N] NAME, TRIGGER, INPUT, PROCESSING LOGIC, OUTPUT, AUDIT ENTRY

Each feature must: have its own Python function/class, write to audit.db on
invocation and completion, and handle errors with a user-facing message.

════════════════════════════════════════════════════════════
CODE REQUIREMENTS
════════════════════════════════════════════════════════════
• Minimum 400 lines. No stubs. Every function fully implemented.
• Structure: imports → constants → PII filter → audit logger →
  Ollama interface → feature functions → TkinterApp class → main()
• Use http.client (stdlib) for the Ollama HTTP call. No requests library.
• Include a requirements comment block listing any 3rd-party packages needed.
• Runnable with: python assistant.py (assuming Ollama is running locally).

════════════════════════════════════════════════════════════
OUTPUT FORMAT
════════════════════════════════════════════════════════════

PRODUCT NAME: [From Stage 1]
BUILD SUMMARY: [2-sentence plain-English description]

OLLAMA MODEL RECOMMENDATION:
  Primary: [model + one-sentence justification]
  Fallback: [model + one-sentence justification]

FEATURE SPECIFICATIONS:
  [5 features in the format above]

FULL PYTHON APPLICATION:
```python
# [Complete runnable application — minimum 400 lines]
```

DEPLOYMENT NOTES:
  [Python version, Ollama setup command, PyInstaller packaging tip,
   first-run checklist, any Tkinter version gotchas]
"""


# ─────────────────────────────────────────────────────────────────────────────
# AI PROVIDER FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

def _is_quota_error(e: Exception) -> bool:
    """Returns True if the exception is a rate-limit or quota exhaustion error."""
    msg = str(e).lower()
    return any(k in msg for k in ("429", "resource_exhausted", "quota", "rate_limit", "too many requests"))


def call_ai_with_fallback(clients: dict, task_prompt: str, label: str = "task") -> str | None:
    """
    Attempts the prompt on Gemini → Groq → Mistral in order.
    - Skips any provider already marked exhausted this session (_EXHAUSTED_PROVIDERS).
    - Permanently marks a provider exhausted on 429 / quota errors so retries
      don't waste time hammering a dead endpoint.
    - Dumps the first 400 chars of every successful response to stdout so you
      can see what the model actually returned (critical for gate debugging).
    Returns the first successful response text, or None if all fail.
    """
    global _EXHAUSTED_PROVIDERS

    # 1. Try Gemini
    if clients.get("gemini") and "gemini" not in _EXHAUSTED_PROVIDERS:
        try:
            print(f"DEBUG: [{label}] Trying Gemini...")
            response = clients["gemini"].models.generate_content(
                model="gemini-2.0-flash", contents=task_prompt
            )
            if response.text:
                audit(label, "success", provider="gemini")
                print(f"DEBUG: [{label}] Gemini response preview:\n{response.text[:400]}\n{'─'*60}")
                return response.text
        except Exception as e:
            if _is_quota_error(e):
                print(f"Gemini QUOTA EXHAUSTED — skipping for the rest of this session.")
                _EXHAUSTED_PROVIDERS.add("gemini")
                audit(label, "quota_exhausted", provider="gemini")
            else:
                print(f"Gemini failed: {e}")
                audit(label, "provider_error", provider="gemini", detail=str(e)[:300])
    elif "gemini" in _EXHAUSTED_PROVIDERS:
        print(f"DEBUG: [{label}] Skipping Gemini (quota exhausted this session).")

    # 2. Try Groq
    if clients.get("groq") and "groq" not in _EXHAUSTED_PROVIDERS:
        try:
            print(f"DEBUG: [{label}] Trying Groq...")
            response = clients["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": task_prompt}]
            )
            text = response.choices[0].message.content
            if text:
                audit(label, "success", provider="groq")
                print(f"DEBUG: [{label}] Groq response preview:\n{text[:400]}\n{'─'*60}")
                return text
        except Exception as e:
            if _is_quota_error(e):
                print(f"Groq QUOTA EXHAUSTED — skipping for the rest of this session.")
                _EXHAUSTED_PROVIDERS.add("groq")
                audit(label, "quota_exhausted", provider="groq")
            else:
                print(f"Groq failed: {e}")
                audit(label, "provider_error", provider="groq", detail=str(e)[:300])
    elif "groq" in _EXHAUSTED_PROVIDERS:
        print(f"DEBUG: [{label}] Skipping Groq (quota exhausted this session).")

    # 3. Try Mistral
    if clients.get("mistral") and "mistral" not in _EXHAUSTED_PROVIDERS:
        try:
            print(f"DEBUG: [{label}] Trying Mistral...")
            response = clients["mistral"].chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": task_prompt}]
            )
            text = response.choices[0].message.content
            if text:
                audit(label, "success", provider="mistral")
                print(f"DEBUG: [{label}] Mistral response preview:\n{text[:400]}\n{'─'*60}")
                return text
        except Exception as e:
            if _is_quota_error(e):
                print(f"Mistral QUOTA EXHAUSTED — skipping for the rest of this session.")
                _EXHAUSTED_PROVIDERS.add("mistral")
                audit(label, "quota_exhausted", provider="mistral")
            else:
                print(f"Mistral failed: {e}")
                audit(label, "provider_error", provider="mistral", detail=str(e)[:300])
    elif "mistral" in _EXHAUSTED_PROVIDERS:
        print(f"DEBUG: [{label}] Skipping Mistral (quota exhausted this session).")

    print(f"CRITICAL: [{label}] All available AI providers failed or are exhausted.")
    audit(label, "all_providers_failed")
    return None


def _check_gate_result(raw: str) -> tuple[bool, str]:
    """
    Robustly determines whether an LLM response represents a gate PASS or FAIL.

    Why this exists: Groq (llama-3.3-70b) frequently ignores exact formatting
    instructions and paraphrases the token we're looking for. This function uses
    multiple detection strategies in priority order so a good idea isn't thrown
    away just because the model wrote "GATE: PASSED" instead of "[GATE: PASS]".

    Returns:
        (passed: bool, reason: str)
    """
    # Normalise for case-insensitive matching
    text_lower = raw.lower()

    # ── Strategy 1: Exact token match (ideal case) ────────────────────────────
    if "[gate: pass]" in text_lower:
        return True, "exact_token"

    # ── Strategy 2: Common Groq paraphrases of PASS ───────────────────────────
    pass_phrases = [
        "gate verdict: pass",
        "gate verdict: [pass]",
        "gate: passed",
        "verdict: pass",
        "all three gates: pass",
        "gate status: pass",
        "passes all three",
        "passes all 3",
        "idea passes",
        "gate check: pass",
    ]
    if any(p in text_lower for p in pass_phrases):
        return True, "fuzzy_pass_phrase"

    # ── Strategy 3: Response contains the expected structured fields ──────────
    # If the model filled out PRODUCT NAME + PROBLEM STATEMENT it almost
    # certainly intended a pass even if it forgot the token.
    required_fields = ["product name:", "problem statement:", "buyer profile:"]
    fields_found = sum(1 for f in required_fields if f in text_lower)
    if fields_found >= 3:
        return True, "structured_fields_present"

    # ── Strategy 4: Explicit FAIL signals ────────────────────────────────────
    if "[gate: fail]" in text_lower:
        reason = raw.split("[GATE: FAIL]")[-1].strip()[:200] if "[GATE: FAIL]" in raw else "model signalled fail"
        return False, reason

    fail_phrases = ["gate verdict: fail", "gate: failed", "verdict: fail", "idea fails"]
    for p in fail_phrases:
        if p in text_lower:
            return False, f"fuzzy_fail_phrase: {p}"

    # ── Strategy 5: Response is suspiciously short (model gave up / confused) ─
    if len(raw.strip()) < 200:
        return False, f"response_too_short ({len(raw.strip())} chars)"

    # ── Default: ambiguous — treat as fail and log the full response for review ─
    return False, f"ambiguous_response — no clear pass/fail signal detected"

# ─────────────────────────────────────────────────────────────────────────────
# TWO-STAGE SCOUT PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_scout_pipeline(clients: dict) -> str | None:
    """
    Runs the two-stage scout pipeline:
      Stage 1: Scout + gate validation (retries up to SCOUT_MAX_RETRIES times).
      Stage 2: Full spec + code generation (only runs on GATE: PASS).

    Returns the full spec+code string on success, or None on total failure.
    """

    # ── STAGE 1: Idea scouting + gate check ──────────────────────────────────
    validation_output = None
    for attempt in range(1, SCOUT_MAX_RETRIES + 1):
        print(f"\n[Scout] Stage 1 — attempt {attempt}/{SCOUT_MAX_RETRIES}: scouting enterprise idea...")
        audit("scout_stage1", "attempt", detail=f"attempt {attempt}")

        raw = call_ai_with_fallback(clients, get_scout_validation_prompt(), label="scout_stage1")

        if not raw:
            print("[Scout] All providers returned nothing. Cannot continue Stage 1.")
            audit("scout_stage1", "no_response")
            break

        passed, reason = _check_gate_result(raw)

        if passed:
            print(f"[Scout] ✅ Gate passed (detection method: {reason}).")
            audit("scout_stage1", "gate_pass", detail=reason)
            validation_output = raw
            break
        else:
            print(f"[Scout] ❌ Gate failed: {reason}")
            audit("scout_stage1", "gate_fail", detail=reason)
            # On ambiguous failures, dump the full raw response so you can
            # inspect what the model actually returned and tune accordingly.
            if "ambiguous" in reason or reason == "unknown":
                print(f"[Scout] Full raw response for inspection:\n{'═'*60}\n{raw}\n{'═'*60}")

    if not validation_output:
        print("[Scout] Could not generate a passing idea after "
              f"{SCOUT_MAX_RETRIES} attempts. Aborting scout pipeline.")
        return None

    # ── STAGE 2: Full spec + code generation ─────────────────────────────────
    print("\n[Scout] Stage 2 — generating full spec and code...")
    audit("scout_stage2", "start")

    spec_output = call_ai_with_fallback(
        clients,
        get_scout_spec_prompt(validation_output),
        label="scout_stage2"
    )

    if not spec_output:
        print("[Scout] Stage 2 failed: all providers returned nothing.")
        audit("scout_stage2", "no_response")
        return None

    audit("scout_stage2", "success", detail=f"output_length={len(spec_output)}")
    print("[Scout] ✅ Stage 2 complete.")
    return spec_output


# ─────────────────────────────────────────────────────────────────────────────
# CODE EXTRACTION HELPER
# ─────────────────────────────────────────────────────────────────────────────

def extract_code_block(text: str) -> str:
    """
    Extracts the Python code from an LLM response.
    Handles:
      - ```python ... ``` fenced blocks (takes the largest one)
      - Bare code with no fencing
    """
    # Find all fenced Python blocks
    fenced = re.findall(r"```python\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fenced:
        # Return the longest block (most likely the full application)
        return max(fenced, key=len).strip()

    # Fallback: strip any remaining backtick fences and return raw text
    return text.replace("```python", "").replace("```", "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# SAVE PRODUCT
# ─────────────────────────────────────────────────────────────────────────────

def save_product(code: str, full_output: str, product_name_hint: str = None) -> str:
    """
    Saves the generated code and full LLM output to the products/ directory.
    Returns the path to the saved assistant.py file.
    """
    timestamp    = int(time.time())
    slug         = re.sub(r"[^a-z0-9]+", "-", (product_name_hint or "desktop-tool").lower())
    folder_name  = f"{slug}-{timestamp}"
    product_dir  = os.path.join(PRODUCTS_DIR, folder_name)

    os.makedirs(product_dir, exist_ok=True)

    # Save the runnable Python file
    code_path = os.path.join(product_dir, "assistant.py")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Save the full LLM output (spec + deployment notes) for reference
    spec_path = os.path.join(product_dir, "spec_output.txt")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(full_output)

    # Write a SHA-256 hash of the generated code for audit integrity
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    audit("save_product", "success", detail=f"path={code_path} sha256={code_hash}")

    return code_path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    init_audit_db()
    clients    = get_clients()
    is_manual  = False
    full_output = None   # Stores the raw LLM response (spec + code combined)
    code        = None
    product_hint = "desktop-tool"

    # ── Check for manual input ────────────────────────────────────────────────
    if os.path.exists(INPUT_IDEA_FILE) and os.path.getsize(INPUT_IDEA_FILE) > 10:
        print("DEBUG: Found manual input. Processing...")
        audit("mode", "manual_input")
        is_manual = True

        with open(INPUT_IDEA_FILE, "r", encoding="utf-8") as f:
            user_idea = f.read().strip()

        task = (
            f"Build a Python/Tkinter desktop app for: {user_idea}. "
            "Follow these requirements strictly:\n"
            "1. Use subprocess to call local Ollama (http://localhost:11434) — "
            "   no external API calls of any kind.\n"
            "2. Include a PII redaction step before any text reaches Ollama "
            "   (strip emails, IPs, SSNs, API keys, JWTs, PEM blocks).\n"
            "3. Run Ollama calls in a background threading.Thread with a "
            "   queue.Queue to return results safely to the Tkinter main loop.\n"
            "4. Show a ttk.Progressbar in indeterminate mode during inference.\n"
            "5. Log every file processed and every Ollama call to audit.db (SQLite).\n"
            "Output ONLY raw Python code — no markdown, no explanation."
        )

        full_output = call_ai_with_fallback(clients, task, label="manual_codegen")
        if full_output:
            code = extract_code_block(full_output)

    else:
        # ── Autonomous scouting mode ──────────────────────────────────────────
        print("DEBUG: No manual input or file empty. Running autonomous scout pipeline...")
        audit("mode", "autonomous_scout")

        full_output = run_scout_pipeline(clients)

        if full_output:
            # Extract the product name for the folder slug
            name_match = re.search(r"PRODUCT NAME:\s*(.+)", full_output)
            if name_match:
                product_hint = name_match.group(1).strip()[:60]

            code = extract_code_block(full_output)

    # ── Validate and save ─────────────────────────────────────────────────────
    if not code or len(code) < 100:
        print("Aborting: No valid code was generated.")
        audit("save_product", "aborted", detail="code empty or too short")
        return

    code_path = save_product(code, full_output or "", product_name_hint=product_hint)
    print(f"\nSUCCESS: Desktop tool deployed to {code_path}")

    # ── Clear manual input file only after confirmed success ──────────────────
    if is_manual:
        with open(INPUT_IDEA_FILE, "w", encoding="utf-8") as f:
            f.write("")
        print("DEBUG: Input file cleared safely.")
        audit("manual_input_clear", "success")


if __name__ == "__main__":
    main()
