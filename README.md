# SafeMigrate: Autonomous SRE Security & Dependency Remediation

> Built for **Hacktoberfest Hack Day Pune** (hosted by **Cloud Native Pune**).  
> Featuring official partner integration with **Kepler by RubixKube**, **Temporal**, and **Gemma 4**.

---

## 💡 The Problem

Traditional dependency management tools (like Dependabot or Renovate) only upgrade manifest version numbers. In production services, upgrading major versions introduces **breaking API changes** (e.g., Pydantic v1 `class Config` ➔ Pydantic v2 `ConfigDict`), resulting in silent build and runtime failures.

**SafeMigrate** bridges the gap between *"dependency upgraded"* and *"codebase adapted to the upgrade"* by combining durable workflow orchestration with system-level AI verification and automated code refactoring.

---

## 🏗️ Architecture & 4-Pillar Integration

```
[ Next.js Control Plane UI ]  <─────── SRE Engineer Interaction
            │
            ▼
   [ Temporal Workflow ] 
            │
            ▼
   [ Gemma 4 AI Engine ]  ── (Reasoning + Search Grounding on CVEs / Breaking Changes)
            │
            ▼
   [ Temporal State: PAUSED (Awaiting Review) ]
            │
            ├──► ⚡ [ Kepler AI IDE ] (Automated Verification & Remediation)
            │         ├─ 1. Run isolated sandbox dry-run (`pytest`, `pip check`)
            │         ├─ 2. Auto-refactor breaking changes (Pydantic v1 ➔ v2 syntax)
            │         └─ 3. Report verification signal back (`engine/signal_kepler.py`)
            │
            ▼
   [ Engineer Clicks 'Approve' ] ──► [ Temporal Resumes & Merges Patch ]
```

### The 4-Pillar Roles:
1. **Temporal**: Orchestrates the durable state machine, handles retries, webhook signals, and ensures zero state loss across pauses.
2. **Gemma 4 AI Engine**: Performs grounded CVE analysis on dependency trees and flags breaking API advisories.
3. **Kepler by RubixKube (SRE AI IDE)**: The automated execution & remediation environment. Kepler runs system-level test dry-runs, parses failure tracebacks, semantically refactors incompatible code, and verifies that the test suite passes before human review.
4. **Next.js Control Plane**: SRE web console to inspect migration status, review diffs, and send approval signals.

---

## 📁 Repository Structure

```
.
├── .kepler/
│   ├── kepler_handoff.json       # Injected state package passed from Temporal to Kepler
│   └── kepler_prompt.md          # Execution prompt for Kepler's automated subagent
├── app/                          # Next.js Control Plane Web Application
│   ├── api/                      # Next.js API routes (migrations & Temporal signals)
│   ├── lib/migration-client.ts   # Client-side API hooks
│   └── page.tsx                  # Interactive SRE Control Plane UI
├── engine/                       # Orchestration & Remediation Engine
│   ├── gemma_analyzer.py         # Gemma 4 CVE grounding & breaking-change detection
│   ├── temporal_workflow.py      # Temporal durable state machine (PAUSED / RESUME)
│   ├── signal_kepler.py          # Emits Kepler verification signal to Temporal
│   └── signal_approve.py         # Emits SRE Human-in-the-Loop approval signal
├── service/                      # Target Microservice needing remediation
│   ├── models.py                 # Service model (initially Pydantic v1 syntax)
│   ├── app.py                    # FastAPI application
│   └── tests/test_models.py      # Pytest test suite executed by Kepler
├── requirements.txt              # Vulnerable dependencies (Pydantic v1, Requests CVE, FastAPI)
├── upgraded_requirements.txt     # Safe upgraded versions formulated by Gemma 4
├── gemma_advisory.json           # Machine-readable CVE & breaking change advisory
└── run_phase_1.py                # CLI runner to trigger Phase 1
```

---

## 🚀 Quickstart & Demo Guide

### Phase 1: Temporal Start & Gemma 4 Security Analysis
Run the orchestrator:
```bash
python run_phase_1.py
```
**What happens:**
- Temporal initializes workflow `sre-cve-remediation-001`.
- Gemma 4 analyzes `requirements.txt`, catches `CVE-2024-37890` (Pydantic) and `CVE-2023-32681` (Requests).
- Gemma 4 flags breaking changes: `class Config` ➔ `model_config = ConfigDict(...)` and `@validator` ➔ `@field_validator`.
- Writes `upgraded_requirements.txt`, `gemma_advisory.json`, and `.kepler/kepler_handoff.json`.
- Temporal workflow safely pauses: `[PAUSED: AWAITING REVIEW]`.

---

### Phase 2: Kepler AI IDE Automated Verification & Remediation
1. Open this repository in the **Kepler AI IDE app**.
2. Run the prompt in Kepler (or follow `.kepler/kepler_prompt.md`):
   ```text
   Run automated verification and refactoring for our dependency upgrade:
   1. Check .kepler/kepler_handoff.json and .kepler/kepler_prompt.md
   2. Run pytest service/tests/test_models.py to observe the failure traces
   3. Refactor service/models.py from Pydantic v1 to Pydantic v2 syntax
   4. Re-run pytest service/tests/test_models.py until all tests pass
   5. Run python engine/signal_kepler.py to signal Temporal
   ```
3. **What Kepler does:**
   - Detects the Pydantic v1 deprecation/failure in `service/tests/test_models.py`.
   - Refactors `service/models.py` into Pydantic v2 syntax.
   - Re-runs tests $\rightarrow$ **`4 passed (100% green)`**.
   - Emits signal `kepler_verification_complete` back to Temporal.

---

### Phase 3: SRE Approval & Merge
Once Kepler's verification report is green, approve the patch:
```bash
python engine/signal_approve.py
```
**Result:** Temporal receives the human approval signal, transitions to `COMPLETED`, merges the patch, and redeploys the service.

---

### Running the Next.js Control Plane UI
To run the SRE Control Plane dashboard:
```bash
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the migration dashboard and trigger approval actions.

---

## 👥 Authors & Acknowledgments

Developed by **Abhinav Mehta** & **Raj Rasane** for **Hacktoberfest Hack Day Pune**, hosted by **Cloud Native Pune**. Special thanks to **RubixKube** for the Kepler AI IDE partner access.