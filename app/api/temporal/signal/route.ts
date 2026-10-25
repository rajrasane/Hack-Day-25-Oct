import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  if (!body.workflow_id || !["APPROVE", "REJECT"].includes(body.action)) {
    return NextResponse.json({ error: "workflow_id and a valid action are required" }, { status: 400 });
  }
  return NextResponse.json({ ok: true, action: body.action });
}
