import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/migrations/${params.id}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to fetch migration status" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({
      workflow_id: params.id,
      temporal_status: "PAUSED_AWAITING_REVIEW",
      note: "Offline fallback state"
    });
  }
}
