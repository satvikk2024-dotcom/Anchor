import { NextRequest, NextResponse } from "next/server";
import { pool } from "@/lib/db";

export async function POST(req: NextRequest) {
  const { applicationId, notes } = await req.json();
  if (!applicationId) {
    return NextResponse.json({ error: "applicationId required" }, { status: 400 });
  }
  await pool.query(
    "UPDATE application SET notes = $1 WHERE id = $2::uuid",
    [notes || null, applicationId]
  );
  return NextResponse.json({ ok: true });
}
