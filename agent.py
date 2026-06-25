import os
import re
import sys
import time
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM

# ==========================================================
# 1. ORCHESTRATION CONFIGURATION & AUTO-HEALING STRATEGIES
# ==========================================================
# Define model combinations in order of preference to bypass API downtime/quotas

FALLBACK_STRATEGIES = [
    {
        "name": "Primary Strategy: Gemini-Flash + Groq",
        "research_model": "gemini/gemini-2.0-flash",
        "coding_model": "groq/llama-3.3-70b-versatile"
    },
    {
        "name": "Secondary Fallback: Pure Groq Architecture",
        "research_model": "groq/llama-3.3-70b-versatile",
        "coding_model": "groq/llama-3.3-70b-versatile"
    },
    {
        "name": "Tertiary Fallback: Mistral + Groq Combination",
        "research_model": "mistral/mistral-large-latest",
        "coding_model": "groq/llama-3.3-70b-versatile"
    }
]

MANUAL_IDEAS_PATH = "manual_ideas.txt"
PRODUCTS_DIR = "products"
JOURNAL_PATH = "MASTER_TREND_JOURNAL.md"


def initialize_llm(model_string: str):
    """Safely initializes an LLM object with basic error handling."""
    return LLM(model=model_string, temperature=0.2)


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

    # The template ships as "LABEL:" lines with nothing after the colon.
    # Only treat this as a real idea if at least one label has an actual
    # value filled in after it (or there's a freeform continuation line).
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


def slugify(text: str, max_words: int = 6) -> str:
    """Turns a freeform title/topic string into a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    words = text.split()[:max_words]
    slug = "-".join(words) if words else "untitled-concept"
    return slug[:60]


def extract_title(markdown_text: str, fallback: str) -> str:
    """Pulls a usable title out of the SEO/research agent's markdown output."""
    for line in markdown_text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line.upper().startswith("PRODUCT NAME:"):
            return line.split(":", 1)[1].strip()
    return fallback


def append_to_journal(title: str, filename: str, source: str):
    """Appends a dated entry to MASTER_TREND_JOURNAL.md so the archive is
    actually a running index, instead of relying on the README's claim alone."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    entry = f"\n## {today} — {title}\n- Source: {source}\n- Output: `products/{filename}`\n"

    mode = "a" if os.path.exists(JOURNAL_PATH) else "w"
    with open(JOURNAL_PATH, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("# Master Trend Journal\n\nRunning archive of every concept TrendForge-AI has produced.\n")
        f.write(entry)


def clear_manual_idea():
    """After a manual idea has been consumed, blank the file so the next run
    falls back to autonomous trend-scouting, as documented in the README."""
    if os.path.exists(MANUAL_IDEAS_PATH):
        with open(MANUAL_IDEAS_PATH, "w", encoding="utf-8") as f:
            f.write("")


# Verify foundational credentials exist before initiating the pipeline execution
if not any([os.environ.get("GEMINI_API_KEY"), os.environ.get("GROQ_API_KEY"), os.environ.get("MISTRAL_API_KEY")]):
    print("❌ CRITICAL ERROR: No operational API keys detected in environment variables.")
    sys.exit(1)


# ==========================================================
# 2. RUNTIME CORE EXECUTION ENGINE
# ==========================================================
def run_agent_pipeline(strategy):
    """Constructs and executes the Crew using the chosen fallback profile."""
    print(f"\n⚙️ Initializing Pipeline using strategy: {strategy['name']}...")

    research_llm = initialize_llm(strategy["research_model"])
    coding_llm = initialize_llm(strategy["coding_model"])
    audit_llm = initialize_llm("mistral/mistral-large-latest")

    manual_idea = read_manual_idea()
    using_manual_idea = manual_idea is not None

    if using_manual_idea:
        print("📌 Manual override detected in manual_ideas.txt — using your idea instead of autonomous scouting.")
        research_description = (
            "A human operator has supplied a specific product concept below. Do NOT invent a "
            "different idea or search for trends. Analyze and structure the following concept "
            "exactly as given, filling in target audience and core value proposition if missing:\n\n"
            f"{manual_idea}"
        )
    else:
        print("🌐 No manual idea found — running fully autonomous trend-scouting mode.")
        research_description = (
            "Scan current digital and market trends broadly (not limited to any single industry) "
            "to find one high-potential, underserved micro-SaaS or tool opportunity. Pick a concrete, "
            "specific niche problem — not a generic category. Identify the target customer and core "
            "value proposition."
        )

    # Construct Specialized Agents
    seo_analyst = Agent(
        role="Lead Market & Trend Research Analyst",
        goal="Identify one concrete, high-potential micro-SaaS or tool opportunity based on real current demand.",
        backstory="Expert data miner who tracks market pain points, search demand, and emerging niches across any industry.",
        llm=research_llm,
        allow_delegation=False,
        verbose=True
    )

    ui_architect = Agent(
        role="Senior Frontend Web Architecture Engineer",
        goal="Transform the researched concept into a clean, dark-themed vanilla HTML/CSS/JS interface tool.",
        backstory="UI layout virtuoso creating modular codebases with embedded browser state management features.",
        llm=coding_llm,
        allow_delegation=False,
        verbose=True
    )

    compliance_auditor = Agent(
        role="Principal System Security & Legal Compliance Auditor",
        goal="Audit code output, implement error handlers, and optimize logic layers for production deployment.",
        backstory="Elite compliance inspector checking framework constraints and handling logic edge cases.",
        llm=audit_llm,
        allow_delegation=False,
        verbose=True
    )

    # Build Tasks with Cross-Model Dependencies
    task_1_research = Task(
        description=research_description,
        expected_output=(
            "Markdown summary starting with a single '# Product Name' line as the title, "
            "followed by target audience, core problem, and value proposition."
        ),
        agent=seo_analyst
    )

    task_2_html = Task(
        description=(
            "Convert the research findings into a functional single-page responsive tracking/utility "
            "workspace app layout. Incorporate a dark corporate styling UI dashboard structure, "
            "localStorage persistence for user inputs, and an audit/lead-capture modal that POSTs to "
            "'https://salarybit.in/api/v1/lead-intake' with a JSON payload identifying which product "
            "concept generated the lead."
        ),
        expected_output="Semantic HTML/JS structural application layout.",
        agent=ui_architect
    )

    # CRITICAL: Explicitly constrains output to a SINGLE file, stopping split code generation
    task_3_audit = Task(
        description=(
            "Combine the design layouts, inline CSS rules, and JavaScript modules into a SINGLE deployable "
            "HTML template file. Embed all styling rules directly into an internal <style> block inside the "
            "document header. Embed all execution logic scripts into a single <script> block right before the "
            "closing body tag. CRITICAL CONSTRAINT: Do not explain the code, do not output distinct file blocks "
            "like index.html or styles.css, and do not write separate files. Output ONLY the raw, unified HTML "
            "layout content. Strip away all markdown code blocks or surrounding ```html syntax markers completely."
        ),
        expected_output="Pure raw single-file deployable HTML source code document text.",
        agent=compliance_auditor
        # NOTE: no fixed output_file here on purpose — the real filename is computed
        # below from the research output, so every run produces a NEW file instead
        # of overwriting the previous day's product.
    )

    # Assemble and trigger sequential execution loop
    orchestrator_crew = Crew(
        agents=[seo_analyst, ui_architect, compliance_auditor],
        tasks=[task_1_research, task_2_html, task_3_audit],
        process=Process.sequential,
        verbose=True
    )

    result = orchestrator_crew.kickoff()

    research_output = str(task_1_research.output) if task_1_research.output else ""
    final_html = str(task_3_audit.output) if task_3_audit.output else str(result)

    fallback_title = "untitled-concept"
    title = extract_title(manual_idea if using_manual_idea else research_output, fallback_title)
    slug = slugify(title)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{slug}-{today_str}.html"

    os.makedirs(PRODUCTS_DIR, exist_ok=True)
    output_path = os.path.join(PRODUCTS_DIR, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    append_to_journal(
        title=title,
        filename=filename,
        source="manual_ideas.txt" if using_manual_idea else "autonomous trend scan"
    )

    if using_manual_idea:
        clear_manual_idea()
        print("🧹 manual_ideas.txt cleared — next run resumes autonomous trend-hunting unless you add a new idea.")

    print(f"\n✅ Wrote new product file: {output_path}")
    return output_path


# ==========================================================
# 3. FAULT-TOLERANT EXECUTOR LOOP
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
