"""Temporal Workflow Implementation for Automated Dependency Remediation.

This module provides:
1. The formal Temporal Workflow definition (`RemediationWorkflow`) and Activities.
2. An interactive Workflow Orchestrator that manages durable state:
   [RUNNING] -> [GEMMA_4_ANALYSIS] -> [PAUSED: AWAITING KEPLER & REVIEW] -> [MERGED]
"""
import os
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from engine.gemma_analyzer import run_gemma_security_analysis


@dataclass
class WorkflowState:
    workflow_id: str
    run_id: str
    status: str  # INITIALIZED, RUNNING, PAUSED_AWAITING_REVIEW, APPROVED, COMPLETED, FAILED
    current_step: str
    gemma_advisory: Optional[Dict[str, Any]] = None
    kepler_verification: Optional[Dict[str, Any]] = None
    human_approved: bool = False
    timestamp: float = 0.0


class DependencyRemediationWorkflow:
    """Temporal durable workflow state machine."""

    def __init__(self, workspace_root: str, workflow_id: str = "sre-cve-remediation-001"):
        self.workspace_root = workspace_root
        self.state = WorkflowState(
            workflow_id=workflow_id,
            run_id=f"run-{int(time.time())}",
            status="INITIALIZED",
            current_step="Pending",
            timestamp=time.time()
        )
        self.state_file = os.path.join(workspace_root, ".temporal_state.json")
        self.kepler_dir = os.path.join(workspace_root, ".kepler")
        os.makedirs(self.kepler_dir, exist_ok=True)

    def persist_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.state), f, indent=2)

    def start_phase_1(self) -> Dict[str, Any]:
        """Executes Phase 1:
        1. Workflow starts
        2. Executes Gemma 4 Reasoning Activity
        3. Prepares Kepler handoff
        4. Transitions to PAUSED_AWAITING_REVIEW
        """
        print("\n" + "=" * 65)
        print(f"[*] [Temporal Workflow: {self.state.workflow_id}] State Machine Starting...")
        print("=" * 65)
        self.state.status = "RUNNING"
        self.state.current_step = "Executing Gemma 4 Security Activity"
        self.persist_state()

        # Activity 1: Run Gemma 4 AI Analysis
        advisory = run_gemma_security_analysis(self.workspace_root)
        self.state.gemma_advisory = advisory

        # Prepare Kepler IDE Handoff Package
        kepler_handoff = {
            "workflow_id": self.state.workflow_id,
            "run_id": self.state.run_id,
            "status": "AWAITING_KEPLER_VERIFICATION",
            "test_command": "pytest service/tests/test_models.py",
            "upgraded_manifest": "upgraded_requirements.txt",
            "target_files_to_inspect": [
                "service/models.py",
                "service/app.py",
                "service/tests/test_models.py"
            ],
            "gemma_advisory": advisory,
            "instructions_for_kepler": [
                "1. Run dry-run test suite using pytest to detect Pydantic v1->v2 breakage.",
                "2. Apply automated semantic refactoring to service/models.py (replace class Config with model_config = ConfigDict(...)).",
                "3. Re-run pytest to verify all tests are green.",
                "4. Emit Kepler verification signal back to Temporal."
            ]
        }

        handoff_path = os.path.join(self.kepler_dir, "kepler_handoff.json")
        with open(handoff_path, "w", encoding="utf-8") as f:
            json.dump(kepler_handoff, f, indent=2)

        # Transition state to PAUSED
        self.state.status = "PAUSED_AWAITING_REVIEW"
        self.state.current_step = "Awaiting Kepler Automated Verification & Human Approval"
        self.persist_state()

        print("\n" + "=" * 65)
        print("[PAUSED] [Temporal Workflow] State: PAUSED (Awaiting Human-in-the-Loop Review)")
        print(f"   Workflow ID : {self.state.workflow_id}")
        print(f"   Run ID      : {self.state.run_id}")
        print(f"   Handoff File: {handoff_path}")
        print("=" * 65)

        return kepler_handoff

    def signal_kepler_verification(self, verification_result: Dict[str, Any]):
        """Signal received from Kepler IDE subagent."""
        print(f"\n[SIGNAL] [Temporal Signal Received] from Kepler AI IDE:")
        print(f"   Tests Passed: {verification_result.get('tests_passed')}")
        print(f"   Refactored Files: {verification_result.get('refactored_files')}")
        self.state.kepler_verification = verification_result
        self.persist_state()

    def signal_human_approval(self, approved: bool = True):
        """Signal received from SRE clicking 'Approve'."""
        if not approved:
            print("\n[-] [Temporal Signal] Human Reviewer Rejected the Patch.")
            self.state.status = "REJECTED"
            self.persist_state()
            return

        print("\n[+] [Temporal Signal] Human Reviewer Approved the Patch.")
        self.state.human_approved = True
        self.state.status = "COMPLETED"
        self.state.current_step = "Patch Merged & Service Redeployed"
        self.persist_state()
        print("[SUCCESS] [Temporal Workflow] Completed Successfully! Patch merged into production branch.")
