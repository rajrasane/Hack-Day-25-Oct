User: # **🚀 1-Hour Execution Cheat-Sheet: Safe Dependency Migration Tool**

---

## **📋 Executive Project Brief (For Submission & Pitch)**

- **Project Title**: **Safe Dependency Migration & Upgrade Tool**
- **Core Objective**: Provide an automated, web-grounded dependency upgrade engine that evaluates breaking changes and security advisories while keeping developers in full control via Human-in-the-Loop approvals.
- **Tech Stack**:

- **Frontend**: Next.js (App Router), React, Tailwind CSS
- **Backend**: Python 3.12 API
- **AI & Intelligence**: **Google Gemma 4** (`gemma-4-26b-a4b-it`) via `@google/genai` / Gemini API + **Google Search Grounding**
- **Workflow Orchestration**: **Temporal** Python SDK (`temporalio`)
- **Partner Integrations**: **JarvisLabs** (Token Factory API) & **Kepler by Rubixkube** (AI IDE)

---

## **🏅 Sponsor Max-Out Points Checklist (For Pitch Lead)**

When presenting to judges, explicitly state how all 4 sponsors are integrated:

1. **Google Gemma 4**: Provides multi-step reasoning (**Thinking Mode**) and live PyPI/npm security advisory lookups (**Google Search Grounding**).
2. **Temporal**: Orchestrates the stateful pipeline and pauses at `AwaitingApprovalState` for Human-in-the-Loop review.
3. **JarvisLabs**: Serves as the hosted open-model inference endpoint for cost and latency benchmarking.
4. **Kepler by Rubixkube**: Functions as the AI IDE environment used by DevOps engineers to safely execute build/test verification commands.

---

## **👥 Person-by-Person Execution Packs**

### **🎨 Person 1: UI & Review Dashboard (You — Full-Stack / UI)**

**Goal**: Build a clean input form, live workflow tracker, side-by-side diff view, and approval trigger.

#### **Action Items:**

1. **Repo Input**: A single URL input field (`"https://github.com/org/repo"`) with a **"Start Migration"** button.
2. **Workflow Progress Tracker**: Render 3 visual badges:

- 🟢 `1. Parsing Manifest`
- 🟡 `2. Gemma 4 Thinking &amp; Grounding...`
- 🔵 `3. Human Review Required`

1. **Diff & Warning Viewer**: Render a side-by-side view comparing original `requirements.txt` vs proposed `upgraded_manifest`, with breaking change warning tags highlighted in red/amber.
2. **Human-in-the-Loop Buttons**:

- **[ Approve & Apply Patch ]**: Calls backend endpoint `/api/temporal/signal` with `action: "APPROVE"`.
- **[ Discard Changes ]**: Calls backend endpoint `/api/temporal/signal` with `action: "REJECT"`.

---

### **🐍 Person 2: Backend Engineer (Python API & File Processing)**

**Goal**: Parse dependency manifests and format clean diffs for the UI.

#### **Action Items:**

1. **File Parsing Helper (** **parser.py** **)**:

```
def parse_requirements(file_content: str) -&gt; list[dict]:
    lines = [l.strip() for l in file_content.splitlines() if l.strip() and not l.startswith('#')]
    deps = []
    for line in lines:
        parts = line.split('==')
        deps.append({
            "package": parts[0],
            "version": parts[1] if len(parts) &gt; 1 else "latest"
        })
    return deps
```

1. **Diff & Output Cleaner**: Ensure Gemma's output JSON is parsed cleanly, validated, and served to the Next.js frontend via a local Fast API/Flask route.

---

### **⚙️ Person 3: Automation & Integration (Temporal & Gemma 4 AI)**

**Goal**: Set up Gemma 4 API calls with Thinking + Search Grounding and wire the Temporal worker.

#### **1. Gemma 4 AI Engine (`gemma_engine.py`):**

```
import os
import json
from google import genai
from google.genai import types

client = genai.Client() # Automatically picks up GEMINI_API_KEY

def analyze_dependencies_with_gemma4(requirements_text: str) -&gt; dict:
    prompt = f"""
    Analyze the following requirements.txt file and propose safe minor/major upgrades.
    Cross-reference live release notes and vulnerability advisories to highlight breaking changes.

    File Content:
    {requirements_text}

    Return strictly valid JSON matching this schema:
    {{
      "upgraded_manifest": "string",
      "breaking_changes": ["string"],
      "security_advisories": ["string"]
    }}
    """

    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="high"),
            tools=[{"google_search": {}}],  # Enable Google Search Grounding
            system_instruction="You are an expert DevOps security auditor. Output valid JSON only."
        )
    )

    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)
```

#### **2. Temporal Human-in-the-Loop Signal Workflow (`workflow.py`):**

```
from temporalio import workflow, activity
from datetime import timedelta

@workflow.defn
class DependencyMigrationWorkflow:
    def __init__(self):
        self.approval_status = None

    @workflow.signal
    def human_review_signal(self, status: str):
        self.approval_status = status

    @workflow.run
    async def run(self, repo_url: str, requirements_text: str):
        # Step 1: AI Analysis
        analysis = await workflow.execute_activity(
            "analyze_activity",
            requirements_text,
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Step 2: Human-in-the-Loop Pause Gate
        await workflow.wait_condition(lambda: self.approval_status is not None)

        if self.approval_status == "APPROVE":
            return {"status": "SUCCESS", "message": "Patch applied successfully!", "data": analysis}
        else:
            return {"status": "REJECTED", "message": "Upgrade discarded by user."}
```

---

### **🧪 Person 4: Research, Testing, Docs & Pitch Lead**

**Goal**: Prepare test data, test prompts in Google AI Studio, write `README.md`, and present the demo.

#### **1. Sample Outdated `requirements.txt` (Copy & Save for Testing):**

```
pydantic==1.10.2
requests==2.25.1
urllib3==1.26.5
flask==2.0.1
```

#### **2. System Prompt for AI Studio Testing:**

> `"You are a senior DevOps dependency security auditor. Analyze the input requirements.txt file. Use Google Search to look up live PyPI release notes and CVE advisories. Identify breaking changes and return a clean JSON object containing upgraded_manifest, breaking_changes, and security_advisories."`

#### **3. 2-Minute Show-and-Tell Demo Script (Practice this now!):**

> **[0:00 - 0:30] Problem**: *"Upgrading project dependencies manually leads to unexpected breaking changes and production outages. Applying automated updates blindly is too risky."*

> **[0:30 - 1:15] Live Demo**: *"We built a safe dependency upgrade tool powered by* **Temporal** *and* **Gemma 4** *. Here, we input a repository URL containing outdated libraries (* *pydantic v1.10* *). Temporal starts the workflow and triggers Gemma 4. Using* **Thinking Mode** *and* **Google Search Grounding** *, Gemma 4 checks live PyPI security advisories in real time."*

> **[1:15 - 1:45] Human-in-the-Loop**: *"Notice that Temporal pauses the execution at* *Awaiting Human Review* *. In our UI, the DevOps engineer sees a side-by-side diff highlighting breaking changes (* *Pydantic v2 migration details* *). We review the verification commands using* **Kepler AI IDE** *, click* *Approve* *, and Temporal resumes to apply the patch."*

> **[1:45 - 2:00] Sponsor Callout & Wrap-up**: *"By combining* **Gemma 4's** *search-grounded reasoning,* **Temporal's** *resilient signal workflows,* **JarvisLabs** *hosted endpoints, and* **Kepler** *, we eliminate blind dependency upgrades!"*

---

🔥 **All 4 team members have their exact roles and ready-to-use code snippets. Let's start building!**

Copilot: Read skill `frontend-design`

I’ll shape this into a focused review cockpit first: inspect the existing app structure, then wire the UI around the migration flow with a distinctive visual system and functional approval interactions.

Find files matching `**/*`

Search for `next|react|tailwind|vite|package.json`

Read 
Completed with input: {
  "path": "/home/raj/Raj/Projects/Hack-Day-25-Oct/README.md"
}

The repository is an empty shell, so I’m going to establish the smallest runnable Next.js App Router surface rather than retrofit an absent stack. The UI will be a dark “mission control” review desk: a repository intake rail, an active Temporal-style timeline, and a dense diff review workspace with a demo mode that can be replaced by the API calls from the brief.

Apply Patch