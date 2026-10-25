"""Temporal Worker for SRE Remediation Pipeline.

Runs workflow and activities connected to local Temporal Server (localhost:7233).
"""
import asyncio
import os
import sys
from datetime import timedelta
from typing import Dict, Any, Optional

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from engine.gemma_analyzer import run_gemma_security_analysis


@activity.defn
async def analyze_dependencies_activity(workspace_dir: str) -> Dict[str, Any]:
    """Gemma 4 security grounding activity."""
    return run_gemma_security_analysis(workspace_dir)


@workflow.defn
class DependencyRemediationWorkflow:
    def __init__(self):
        self.status = "INITIALIZED"
        self.gemma_advisory: Optional[Dict[str, Any]] = None
        self.kepler_verification: Optional[Dict[str, Any]] = None
        self.human_approved: bool = False
        self.workspace_dir: str = ""

    @workflow.signal
    def kepler_verification(self, verification_payload: Dict[str, Any]):
        """Signal received from Kepler AI IDE."""
        self.kepler_verification = verification_payload
        self.status = "VERIFIED_BY_KEPLER_AWAITING_HUMAN"

    @workflow.signal
    def human_approval(self, approved: bool):
        """Signal received from SRE clicking Approve in the UI."""
        self.human_approved = approved
        self.status = "APPROVED_MERGING" if approved else "REJECTED"

    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "gemma_advisory": self.gemma_advisory,
            "kepler_verification": self.kepler_verification,
            "human_approved": self.human_approved,
        }

    @workflow.run
    async def run(self, workspace_dir: str) -> Dict[str, Any]:
        self.workspace_dir = workspace_dir
        self.status = "ANALYZING_DEPENDENCIES"

        # 1. Execute Gemma 4 Analysis Activity
        self.gemma_advisory = await workflow.execute_activity(
            analyze_dependencies_activity,
            workspace_dir,
            start_to_close_timeout=timedelta(minutes=2),
        )

        # 2. Transition to PAUSED state
        self.status = "PAUSED_AWAITING_KEPLER_VERIFICATION"

        # 3. Wait for Kepler Verification Signal (or human approval directly)
        await workflow.wait_condition(
            lambda: self.kepler_verification is not None or self.human_approved
        )

        # 4. Wait for Human Approval
        if not self.human_approved:
            self.status = "AWAITING_HUMAN_APPROVAL"
            await workflow.wait_condition(lambda: self.human_approved is True)

        self.status = "COMPLETED"
        return {
            "workflow_status": "COMPLETED",
            "kepler_verified": bool(self.kepler_verification),
            "human_approved": self.human_approved,
        }


async def run_worker():
    print("[*] Connecting Worker to Temporal Server at localhost:7233...")
    client = await Client.connect("localhost:7233")
    print("[+] Worker connected to Temporal!")

    worker = Worker(
        client,
        task_queue="sre-remediation-task-queue",
        workflows=[DependencyRemediationWorkflow],
        activities=[analyze_dependencies_activity],
    )

    print("[+] Temporal Worker is listening on queue: sre-remediation-task-queue")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
