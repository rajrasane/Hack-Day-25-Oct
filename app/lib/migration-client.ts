export type MigrationRequest = {
  repo_url: string;
  config_path: string;
  project_type: string;
};

export type MigrationResponse = {
  workflow_id: string;
  status: "REVIEW_READY" | "RUNNING";
};

export type SignalResponse = { ok: boolean; action: "APPROVE" | "REJECT" };

export async function startMigration(payload: MigrationRequest): Promise<MigrationResponse> {
  const response = await fetch("/api/migrations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error("We could not start this migration.");
  return response.json();
}

export async function sendMigrationSignal(workflowId: string, action: "APPROVE" | "REJECT"): Promise<SignalResponse> {
  const response = await fetch("/api/temporal/signal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workflow_id: workflowId, action })
  });
  if (!response.ok) throw new Error("We could not update the migration.");
  return response.json();
}
