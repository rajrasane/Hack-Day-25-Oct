import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  if (!body.repo_url || !body.config_path || !body.project_type) {
    return NextResponse.json({ error: "repo_url, config_path, and project_type are required" }, { status: 400 });
  }
  return NextResponse.json({ workflow_id: `migration-${Date.now()}`, status: "REVIEW_READY" });
}
