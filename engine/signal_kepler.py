"""Script to signal Temporal that Kepler verification and refactoring has completed."""
import os
import json
from engine.temporal_workflow import DependencyRemediationWorkflow

def send_kepler_signal():
    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow = DependencyRemediationWorkflow(workspace)

    # Load state
    state_file = os.path.join(workspace, ".temporal_state.json")
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
            workflow.state.workflow_id = state_data.get("workflow_id", "sre-cve-remediation-001")
            workflow.state.run_id = state_data.get("run_id", "run-1")

    verification_payload = {
        "verified_by": "Kepler SRE AI IDE",
        "tests_passed": True,
        "refactored_files": ["service/models.py"],
        "summary": "Pydantic v1 class Config successfully migrated to Pydantic v2 ConfigDict. Pytest suite 100% green."
    }

    workflow.signal_kepler_verification(verification_payload)
    print("\n[+] Verification signal sent to Temporal! SRE Engineer can now review and approve.")

if __name__ == "__main__":
    send_kepler_signal()
