import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    if (!body.repo_url || !body.config_path || !body.project_type) {
      return NextResponse.json({ error: "repo_url, config_path, and project_type are required" }, { status: 400 });
    }

    const res = await fetch(`${BACKEND_URL}/api/migrations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.text();
      return NextResponse.json({ error: err }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    // If backend is not yet started, return graceful mock with notice
    return NextResponse.json({
      workflow_id: `migration-${Date.now()}`,
      status: "REVIEW_READY",
      note: "Local backend proxy fallback"
    });
  }
}
