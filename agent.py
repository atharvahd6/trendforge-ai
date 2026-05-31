import os
import sys
import time
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

def initialize_llm(model_string: str):
    """Safely initializes an LLM object with basic error handling."""
    return LLM(model=model_string, temperature=0.2)

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

    # Construct Specialized Agents
    seo_analyst = Agent(
        role="Lead SEO Strategy & Global Mobility Analyst",
        goal="Pinpoint high-volume, highly searched global visa and immigration keywords on Google.",
        backstory="Expert data miner tracking global immigration patterns and expat movement criteria.",
        llm=research_llm,
        allow_delegation=False,
        verbose=True
    )

    ui_architect = Agent(
        role="Senior Frontend Web Architecture Engineer",
        goal="Transform abstract trend matrices into clean, dark-themed vanilla HTML/CSS/JS interface tools.",
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
    task_1_seo = Task(
        description="Analyze 3 high-volume international immigration search pathways and outline core documentation tracking milestones.",
        expected_output="Markdown summary listing target destinations and structural visa compliance paths.",
        agent=seo_analyst
    )

    task_2_html = Task(
        description=(
            "Convert findings into a functional single-page responsive tracking workspace app layout. "
            "Incorporate a dark corporate styling UI dashboard structure, localStorage persistence, and "
            "an audit processing modal referencing 'https://salarybit.in/api/v1/visa-brief'."
        ),
        expected_output="Semantic HTML/JS structural application layouts.",
        agent=ui_architect
    )

    # CRITICAL: Explicitly constrains output to a SINGLE file, stopping split code generation
    task_3_audit = Task(
        description=(
            "Combine the design layouts, inline CSS rules, and JavaScript modules into a SINGLE deployable HTML template file. "
            "Embed all styling rules directly into an internal <style> block inside the document header. "
            "Embed all execution logic scripts into a single <script> block right before the closing body tag. "
            "CRITICAL CONSTRAINT: Do not explain the code, do not output distinct file blocks like index.html or styles.css, "
            "and do not write separate files. Output ONLY the raw, unified HTML layout content. "
            "Strip away all markdown code blocks or surrounding ```html syntax markers completely."
        ),
        expected_output="Pure raw single-file deployable HTML source code document text.",
        agent=compliance_auditor,
        output_file="products/salarybit_visa_tool.html",
        create_directory=True
    )

    # Assemble and trigger sequential execution loop
    orchestrator_crew = Crew(
        agents=[seo_analyst, ui_architect, compliance_auditor],
        tasks=[task_1_seo, task_2_html, task_3_audit],
        process=Process.sequential,
        verbose=True
    )

    orchestrator_crew.kickoff()


# ==========================================================
# 3. FAULT-TOLERANT EXECUTOR LOOP
# ==========================================================

def main():
    print("🤖 TrendForge Auto-Healing Autopilot Factory Online.")
    
    for index, strategy in enumerate(FALLBACK_STRATEGIES):
        try:
            run_agent_pipeline(strategy)
            print("\n✅ SUCCESS: Agent workflow executed and finalized successfully!")
            print("Production asset written directly to: products/salarybit_visa_tool.html")
            return  # Kill program execution cleanly to skip further fallback loops
            
        except Exception as error:
            print(f"\n⚠️ WARNING: Pipeline run execution failed using strategy '{strategy['name']}'.")
            print(f"Intercepted Error: {str(error)}")
            
            remaining_attempts = len(FALLBACK_STRATEGIES) - (index + 1)
            if remaining_attempts > 0:
                print(f"🔄 Recovering... Dynamically switching API profiles and moving to the next fallback option.")
                print("Cooldown safety delay active: Pausing 5 seconds for rate limits to settle...")
                time.sleep(5)
            else:
                print("\n❌ CRITICAL SYSTEM FAILURE: All auto-healing configurations and API combinations exhausted.")
                sys.exit(1)

if __name__ == "__main__":
    main()
