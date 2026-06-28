import { NextRequest, NextResponse } from "next/server";
import { pool } from "@/lib/db";

const VALID_STATUSES = [
  "intake_received",
  "researched",
  "low_match_waiting",
  "awaiting_review",
  "submitted",
  "responded",
  "interview",
  "rejected",
  "ghosted",
  "withdrawn",
  "errored",
];

export async function POST(req: NextRequest) {
  const { applicationId, status } = await req.json();

  if (!applicationId || !VALID_STATUSES.includes(status)) {
    return NextResponse.json(
      { error: "Invalid applicationId or status" },
      { status: 400 }
    );
  }

  const extra =
    status === "submitted"
      ? ", submitted_at = now()"
      : status === "responded"
        ? ", responded_at = now()"
        : "";

  await pool.query(
    `UPDATE application SET status = $1${extra} WHERE id = $2::uuid`,
    [status, applicationId]
  );

  return NextResponse.json({ ok: true, status });
}
