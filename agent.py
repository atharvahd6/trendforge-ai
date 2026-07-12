import os
import re
import sys
import time
from datetime import datetime

# ==========================================================
# 1. ORCHESTRATION CONFIGURATION & AUTO-HEALING STRATEGIES
# ==========================================================
# Each strategy names which provider handles research vs coding vs audit.
# No agent framework is used here on purpose — requirements.txt only ships
# google-genai, groq, and mistralai, so this calls each SDK directly.

FALLBACK_STRATEGIES = [
    {
        "name": "Primary Strategy: Gemini + Groq",
        "research_provider": "gemini",
        "coding_provider": "groq",
    },
    {
        "name": "Secondary Fallback: Pure Groq",
        "research_provider": "groq",
        "coding_provider": "groq",
    },
    {
        "name": "Tertiary Fallback: Mistral + Groq",
        "research_provider": "mistral",
        "coding_provider": "groq",
    },
]

GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
MISTRAL_MODEL = "mistral-large-latest"

MANUAL_IDEAS_PATH = "manual_ideas.txt"
PRODUCTS_DIR = "products"
JOURNAL_PATH = "MASTER_TREND_JOURNAL.md"
INDEX_PATH = "index.html"

JOURNAL_HEADER = (
    "# 📚 Master Autonomous Trend Journal\n\n"
    "| Date Run | Discovered Startup Concept | Live Web App Link |\n"
    "| :--- | :--- | :--- |\n"
)

GITHUB_PAGES_BASE = "https://atharvahd6.github.io/trendforge-ai/products"


# ==========================================================
# 2. PROVIDER CALL WRAPPERS (direct SDK usage, no framework)
# ==========================================================
def call_gemini(prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def call_groq(prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
        temperature=0.2,
    )
    return completion.choices[0].message.content


def call_mistral(prompt: str) -> str:
    # mistralai changed its import path in v2.0 (from mistralai import Mistral ->
    # from mistralai.client import Mistral). Support both so this works regardless
    # of which version pip resolves.
    try:
        from mistralai import Mistral
    except ImportError:
        from mistralai.client import Mistral

    with Mistral(api_key=os.environ["MISTRAL_API_KEY"]) as client:
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
    return response.choices[0].message.content


PROVIDER_CALLERS = {
    "gemini": call_gemini,
    "groq": call_groq,
    "mistral": call_mistral,
}


def call_provider(provider: str, prompt: str) -> str:
    return PROVIDER_CALLERS[provider](prompt)


# ==========================================================
# 3. MANUAL OVERRIDE HANDLING
# ==========================================================
def read_manual_idea():
    """
    Reads manual_ideas.txt if present. Returns the stripped content if it
    contains a real idea, or None if the file is missing, empty, or only
    contains the documented placeholder template (so autonomous mode resumes).
    """
    if not os.path.exists(MANUAL_IDEAS_PATH):
        return None

    with open(MANUAL_IDEAS_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return None

    has_real_value = False
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            _, _, value = line.partition(":")
            if value.strip():
                has_real_value = True
                break
        elif not line.upper().endswith(":"):
            has_real_value = True
            break

    if not has_real_value:
        return None

    return content


def clear_manual_idea():
    """After a manual idea has been consumed, blank the file so the next run
    falls back to autonomous trend-scouting, as documented in the README."""
    if os.path.exists(MANUAL_IDEAS_PATH):
        with open(MANUAL_IDEAS_PATH, "w", encoding="utf-8") as f:
            f.write("")


# ==========================================================
# 4. TEXT / FILE HELPERS
# ==========================================================
def slugify(text: str, max_words: int = 12) -> str:
    """Turns a freeform title/topic string into a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    words = text.split()[:max_words]
    slug = "-".join(words) if words else "untitled-concept"
    return slug[:60]


def extract_title(text: str, fallback: str) -> str:
    """Pulls a usable product title out of research output or a manual idea block."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line.upper().startswith("PRODUCT NAME:"):
            value = line.split(":", 1)[1].strip()
            if value:
                return value
    return fallback


def strip_code_fences(html_text: str) -> str:
    """Models sometimes wrap output in ```html ... ``` even when told not to."""
    text = html_text.strip()
    text = re.sub(r"^```(?:html)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def ensure_journal_exists():
    if not os.path.exists(JOURNAL_PATH):
        with open(JOURNAL_PATH, "w", encoding="utf-8") as f:
            f.write(JOURNAL_HEADER)


def read_journal_rows():
    """Parses existing markdown table rows out of MASTER_TREND_JOURNAL.md.
    Returns a list of (date, concept, link) tuples, oldest first."""
    ensure_journal_exists()
    rows = []
    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != 3:
                continue
            if cells[0].lower() in ("date run", ":---"):
                continue
            rows.append(tuple(cells))
    return rows


def append_journal_row(date_str: str, title: str, link: str):
    ensure_journal_exists()
    with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
        f.write(f"| {date_str} | {title} | {link} |\n")


def extract_link_url(link_markdown: str) -> str:
    """Pulls the raw URL out of a markdown link cell like
    '[Launch App Tool 🌐](https://...)' so it can be re-templated into HTML."""
    match = re.search(r"\((https?://[^)]+)\)", link_markdown)
    return match.group(1) if match else "#"


def get_recent_titles(limit: int = 15):
    """Returns the most recent product titles from the journal, newest first.
    Used to stop the Trend Scout from re-pitching a concept it already shipped."""
    rows = read_journal_rows()
    titles = [title for (_date, title, _link) in rows]
    return list(reversed(titles))[:limit]


def render_index_html(rows):
    """Rebuilds index.html from journal rows, keeping the exact same dark
    dashboard styling that was already hand-built — only the <tbody> changes."""
    row_html_blocks = []
    for date_str, title, link_markdown in rows:
        url = extract_link_url(link_markdown)
        row_html_blocks.append(f"""
            <tr>
                <td>{date_str}</td>
                <td style="font-weight:600; color:#fff;">{title}</td>
                <td><a href="{url}" target="_blank" style="color:#10B981; text-decoration:none; font-weight:bold;">Launch App Tool 🌐</a></td>
            </tr>""")
    rows_html = "".join(row_html_blocks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrendForge Venture Lab</title>
    <style>
        :root {{
            --bg-main: #0B0F19;
            --bg-card: #151D30;
            --accent: #38BDF8;
            --text-main: #F3F4F6;
            --text-muted: #9CA3AF;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            margin: 0; padding: 0; line-height: 1.6;
        }}
        header {{
            max-width: 1100px; margin: 0 auto; padding: 4rem 2rem 2rem 2rem; text-align: center;
        }}
        h1 {{
            font-size: 3rem; font-weight: 800; margin-bottom: 0.5rem;
            background: linear-gradient(to right, #38BDF8, #818CF8);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: var(--text-muted); font-size: 1.2rem; max-width: 700px; margin: 0 auto; }}
        main {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
        .table-container {{
            background-color: var(--bg-card); border-radius: 12px; padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.05); overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        th {{ color: var(--accent); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em; }}
    </style>
</head>
<body>
    <header>
        <h1>TrendForge Venture Lab</h1>
        <p class="subtitle">Every 24 hours, this lab deploys a 100% complete, functional, ready-to-use web tool to solve real digital constraints immediately.</p>
    </header>
    <main>
        <h2 style="font-size:1.5rem; margin-bottom:1rem;">📚 Live Operational Product Ledger</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date Run</th>
                        <th>Discovered Startup Concept</th>
                        <th>Live Web App Link</th>
                    </tr>
                </thead>
                <tbody>{rows_html}
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>"""


def rebuild_index_html():
    rows = read_journal_rows()
    html = render_index_html(rows)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)


# Verify foundational credentials exist before initiating the pipeline execution
if not any([os.environ.get("GEMINI_API_KEY"), os.environ.get("GROQ_API_KEY"), os.environ.get("MISTRAL_API_KEY")]):
    print("❌ CRITICAL ERROR: No operational API keys detected in environment variables.")
    sys.exit(1)


# ==========================================================
# 5. RUNTIME CORE EXECUTION ENGINE
# ==========================================================
def run_agent_pipeline(strategy):
    """Runs research -> code -> audit sequentially using direct SDK calls."""
    print(f"\n⚙️ Initializing Pipeline using strategy: {strategy['name']}...")

    manual_idea = read_manual_idea()
    using_manual_idea = manual_idea is not None

    if using_manual_idea:
        print("📌 Manual override detected in manual_ideas.txt — using your idea instead of autonomous scouting.")
        research_prompt = (
            "A human operator has supplied a specific product concept below. Do NOT invent a "
            "different idea or search for trends. Restructure the following concept into a short "
            "markdown brief that starts with a single '# Product Name' line as the title, followed "
            "by target audience, core problem, and value proposition:\n\n"
            f"{manual_idea}"
        )
    else:
        print("🌐 No manual idea found — running fully autonomous trend-scouting mode.")

        # BUGFIX: previously the model was given no memory of what it had
        # already shipped, so with a narrow prompt it kept converging on the
        # same comfortable idea run after run (e.g. nine "content calendar"
        # variants in twelve days). Pulling recent titles from the journal
        # and explicitly banning repeats/close variants forces real variety.
        recent_titles = get_recent_titles(limit=15)
        if recent_titles:
            recent_titles_block = "\n".join(f"- {t}" for t in recent_titles)
            avoid_clause = (
                "\n\nThe following concepts have ALREADY been built recently. Do NOT repeat any "
                "of them, and do NOT propose a close variant that just swaps the target audience "
                "or industry for the same underlying tool (e.g. do not submit another 'content "
                "calendar for <different audience>' if one is already listed below). Pick a "
                "genuinely different underlying problem and mechanism:\n"
                f"{recent_titles_block}"
            )
        else:
            avoid_clause = ""

        research_prompt = (
            "Identify one concrete, high-potential, underserved micro-SaaS or single-page tool "
            "opportunity based on current digital trends (not limited to any single industry). "
            "Pick a specific niche problem, not a generic category. Respond in markdown starting "
            "with a single '# Product Name' line as the title, followed by target audience, core "
            "problem, and value proposition."
            f"{avoid_clause}"
        )

    research_output = call_provider(strategy["research_provider"], research_prompt)

    coding_prompt = (
        "Convert the following product brief into a functional, responsive, single-page dark-themed "
        "HTML/CSS/JS tool. Include localStorage persistence for user inputs and a lead-capture modal "
        "that POSTs to 'https://salarybit.in/api/v1/lead-intake' with a JSON payload identifying the "
        "product concept. CRITICAL CONSTRAINT: output ONLY the raw HTML document — a single file with "
        "an internal <style> block and a single <script> block before the closing </body> tag. Do not "
        "explain anything, do not output multiple files, and do not wrap the output in markdown code "
        "fences.\n\nProduct brief:\n\n"
        f"{research_output}"
    )
    coded_html = call_provider(strategy["coding_provider"], coding_prompt)

    audit_prompt = (
        "Audit and clean up the following HTML document for production deployment: fix any broken "
        "tags, add basic error handling around localStorage and fetch calls, and ensure it is a single "
        "complete, valid HTML document. CRITICAL CONSTRAINT: output ONLY the raw, corrected HTML — no "
        "explanation, no markdown code fences, no separate files.\n\nHTML to audit:\n\n"
        f"{coded_html}"
    )
    # Audit always runs on Mistral regardless of strategy, mirroring the original
    # compliance-auditor role being a fixed model rather than part of the fallback swap.
    final_html = call_provider("mistral", audit_prompt)
    final_html = strip_code_fences(final_html)

    fallback_title = "untitled-concept"
    title = extract_title(manual_idea if using_manual_idea else research_output, fallback_title)
    slug = slugify(title)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # BUGFIX: previously the folder was named `products/{slug}` with no date
    # prefix. Because slugify() only kept the first 6 words, near-identical
    # titles (e.g. two different "...Content Calendar for X" ideas) collapsed
    # to the SAME slug, and os.makedirs(..., exist_ok=True) silently reused
    # that folder — so every colliding run overwrote the previous day's live
    # index.html at the same URL instead of archiving it. Prefixing with the
    # run date guarantees a fresh, permanent folder every single run, and the
    # while-loop below still protects against two runs on the same UTC day.
    base_slug = f"{today_str}-{slug}"
    dated_slug = base_slug
    suffix = 2
    while os.path.exists(os.path.join(PRODUCTS_DIR, dated_slug)):
        dated_slug = f"{base_slug}-{suffix}"
        suffix += 1
    slug = dated_slug

    product_dir = os.path.join(PRODUCTS_DIR, slug)
    os.makedirs(product_dir, exist_ok=True)
    output_path = os.path.join(product_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    live_url = f"{GITHUB_PAGES_BASE}/{slug}/"
    link_markdown = f"[Launch App Tool 🌐]({live_url})"
    append_journal_row(today_str, title, link_markdown)
    rebuild_index_html()

    if using_manual_idea:
        clear_manual_idea()
        print("🧹 manual_ideas.txt cleared — next run resumes autonomous trend-hunting unless you add a new idea.")

    print(f"\n✅ Wrote new product file: {output_path}")
    print(f"✅ Updated journal and regenerated {INDEX_PATH}")
    print(f"🔗 Will be live at: {live_url} (once GitHub Pages picks up the new commit)")
    return output_path


# ==========================================================
# 6. FAULT-TOLERANT EXECUTOR LOOP
# ==========================================================
def main():
    print("🤖 TrendForge Auto-Healing Autopilot Factory Online.")

    for index, strategy in enumerate(FALLBACK_STRATEGIES):
        try:
            output_path = run_agent_pipeline(strategy)
            print("\n✅ SUCCESS: Agent workflow executed and finalized successfully!")
            print(f"Production asset written to: {output_path}")
            return  # Kill program execution cleanly to skip further fallback loops
        except Exception as error:
            print(f"\n⚠️ WARNING: Pipeline run execution failed using strategy '{strategy['name']}'.")
            print(f"Intercepted Error: {str(error)}")
            remaining_attempts = len(FALLBACK_STRATEGIES) - (index + 1)
            if remaining_attempts > 0:
                print("🔄 Recovering... Dynamically switching API profiles and moving to the next fallback option.")
                print("Cooldown safety delay active: Pausing 5 seconds for rate limits to settle...")
                time.sleep(5)
            else:
                print("\n❌ CRITICAL SYSTEM FAILURE: All auto-healing configurations and API combinations exhausted.")
                sys.exit(1)


if __name__ == "__main__":
    main()
