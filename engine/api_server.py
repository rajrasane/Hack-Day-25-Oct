"""FastAPI Backend Server bridging Frontend to Local Temporal Server.

Endpoints:
- POST /api/migrations: Starts Temporal workflow
- GET  /api/migrations/{id}: Returns live status, manifests, and CVE analysis
- POST /api/temporal/signal: Sends APPROVE / REJECT signal to Temporal
- POST /api/temporal/signal-kepler: Sends Kepler test verification signal
"""
import os
import sys
import json
import time
import asyncio
from typing import Optional

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from temporalio.client import Client

from engine.worker import DependencyRemediationWorkflow

app = FastAPI(title="SafeMigrate SRE Control Plane Backend")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
temporal_client: Optional[Client] = None


async def get_temporal_client() -> Client:
    global temporal_client
    if temporal_client is None:
        try:
            temporal_client = await Client.connect("localhost:7233")
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Could not connect to Temporal Server at localhost:7233: {str(e)}"
            )
    return temporal_client


class MigrationStartRequest(BaseModel):
    repo_url: str
    config_path: str = "requirements.txt"
    project_type: str = "Python"


class SignalRequest(BaseModel):
    workflow_id: str
    action: str  # "APPROVE" or "REJECT"


class KeplerSignalRequest(BaseModel):
    workflow_id: str
    tests_passed: bool
    refactored_files: list[str]
    summary: str


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "SafeMigrate Backend", "temporal": "localhost:7233"}


@app.post("/api/migrations")
async def start_migration(req: MigrationStartRequest):
    client = await get_temporal_client()
    workflow_id = f"sre-migration-{int(time.time())}"

    try:
        handle = await client.start_workflow(
            DependencyRemediationWorkflow.run,
            WORKSPACE_ROOT,
            id=workflow_id,
            task_queue="sre-remediation-task-queue",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Temporal workflow: {e}")

    # Give workflow a moment to run the activity
    await asyncio.sleep(0.5)

    return {
        "workflow_id": workflow_id,
        "run_id": handle.result_run_id,
        "status": "RUNNING",
        "message": "Temporal workflow successfully started."
    }


@app.get("/api/migrations/{workflow_id}")
async def get_migration_status(workflow_id: str):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        status_data = await handle.query(DependencyRemediationWorkflow.get_status)
    except Exception as e:
        # If workflow query is not yet available, fallback gracefully
        status_data = {"status": "INITIALIZED", "error": str(e)}

    # Read real manifest files
    orig_req_path = os.path.join(WORKSPACE_ROOT, "requirements.txt")
    upgraded_req_path = os.path.join(WORKSPACE_ROOT, "upgraded_requirements.txt")
    advisory_path = os.path.join(WORKSPACE_ROOT, "gemma_advisory.json")

    original_manifest = ""
    upgraded_manifest = ""
    advisory = None

    if os.path.exists(orig_req_path):
        with open(orig_req_path, "r", encoding="utf-8") as f:
            original_manifest = f.read()

    if os.path.exists(upgraded_req_path):
        with open(upgraded_req_path, "r", encoding="utf-8") as f:
            upgraded_manifest = f.read()

    if os.path.exists(advisory_path):
        with open(advisory_path, "r", encoding="utf-8") as f:
            advisory = json.load(f)

    return {
        "workflow_id": workflow_id,
        "temporal_status": status_data.get("status", "RUNNING"),
        "original_manifest": original_manifest,
        "upgraded_manifest": upgraded_manifest,
        "gemma_advisory": status_data.get("gemma_advisory") or advisory,
        "kepler_verification": status_data.get("kepler_verification"),
        "human_approved": status_data.get("human_approved", False)
    }


@app.post("/api/temporal/signal")
async def send_signal(req: SignalRequest):
    if req.action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")

    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(req.workflow_id)
        await handle.signal(
            DependencyRemediationWorkflow.human_approval,
            req.action == "APPROVE"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to signal Temporal: {e}")

    return {"ok": True, "action": req.action, "workflow_id": req.workflow_id}


@app.post("/api/temporal/signal-kepler")
async def send_kepler_signal_api(req: KeplerSignalRequest):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(req.workflow_id)
        await handle.signal(
            DependencyRemediationWorkflow.kepler_verification,
            {
                "verified_by": "Kepler SRE AI IDE",
                "tests_passed": req.tests_passed,
                "refactored_files": req.refactored_files,
                "summary": req.summary,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to signal Kepler status: {e}")

    return {"ok": True, "status": "VERIFIED_BY_KEPLER", "workflow_id": req.workflow_id}


if __name__ == "__main__":
    import uvicorn
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=8000)
