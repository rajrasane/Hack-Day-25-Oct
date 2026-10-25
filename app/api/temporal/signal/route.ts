import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    if (!body.workflow_id || !["APPROVE", "REJECT"].includes(body.action)) {
      return NextResponse.json({ error: "workflow_id and a valid action are required" }, { status: 400 });
    }

    const res = await fetch(`${BACKEND_URL}/api/temporal/signal`, {
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
    // If backend is running standalone or offline fallback
    return NextResponse.json({ ok: true, action: "APPROVE", fallback: true });
  }
}
