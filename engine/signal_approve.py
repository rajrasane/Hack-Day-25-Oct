"""Script to simulate the SRE Engineer clicking 'Approve' to resume Temporal and merge patch."""
import os
import json
from engine.temporal_workflow import DependencyRemediationWorkflow

def approve():
    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow = DependencyRemediationWorkflow(workspace)

    state_file = os.path.join(workspace, ".temporal_state.json")
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
            workflow.state.workflow_id = state_data.get("workflow_id", "sre-cve-remediation-001")
            workflow.state.run_id = state_data.get("run_id", "run-1")

    workflow.signal_human_approval(approved=True)

if __name__ == "__main__":
    approve()
