import { pool } from "./db";
import type {
  ApplicationRow,
  AgentRunRow,
  WeeklyInsightRow,
  ApplicationStatus,
  MasterResumeEntry,
  UserProfile,
} from "./types";

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  "intake_received",
  "researched",
  "low_match_waiting",
  "awaiting_review",
  "submitted",
  "responded",
  "interview",
  "rejected",
  "ghosted",
  "errored",
  "withdrawn",
];

export async function getApplications(): Promise<ApplicationRow[]> {
  const { rows } = await pool.query<ApplicationRow>(`
    SELECT
      a.id, a.url, a.company_id, c.name AS company_name,
      a.role_title, a.status, a.match_score,
      a.created_at, a.submitted_at, a.responded_at, a.follow_up_window_days
    FROM application a
    LEFT JOIN company c ON c.id = a.company_id
    ORDER BY a.created_at DESC
  `);
  return rows;
}

// Groups the flat list into a Record<ApplicationStatus, ApplicationRow[]> for the
// kanban — a single query plus pure-JS grouping, rather than 11 per-status queries.
export function groupByStatus(
  applications: ApplicationRow[]
): Record<ApplicationStatus, ApplicationRow[]> {
  const grouped = Object.fromEntries(
    APPLICATION_STATUSES.map((status) => [status, [] as ApplicationRow[]])
  ) as Record<ApplicationStatus, ApplicationRow[]>;

  for (const app of applications) {
    grouped[app.status].push(app);
  }
  return grouped;
}

export async function getAgentRuns(): Promise<AgentRunRow[]> {
  const { rows } = await pool.query<AgentRunRow>(`
    SELECT
      ar.id, ar.application_id, c.name AS company_name, a.role_title,
      ar.workflow_name, ar.agent_name, ar.input_hash, ar.output_json,
      ar.latency_ms, ar.critic_passed, ar.created_at
    FROM agent_run ar
    LEFT JOIN application a ON a.id = ar.application_id
    LEFT JOIN company c ON c.id = a.company_id
    ORDER BY ar.created_at DESC
  `);
  return rows;
}

export async function getApplicationDetail(id: string) {
  const { rows: [app] } = await pool.query(`
    SELECT a.id, a.url, a.role_title, a.status, a.match_score,
           a.created_at, a.submitted_at, a.responded_at, a.follow_up_window_days,
           a.notes, c.name AS company_name, c.synthesis
    FROM application a
    LEFT JOIN company c ON c.id = a.company_id
    WHERE a.id = $1
  `, [id]);
  if (!app) return null;

  const { rows: materials } = await pool.query(`
    SELECT id, type, content_json, content_rendered, pdf_drive_url, generated_at
    FROM generated_material WHERE application_id = $1
    ORDER BY generated_at
  `, [id]);

  const { rows: agentRuns } = await pool.query(`
    SELECT agent_name, workflow_name, output_json, latency_ms, critic_passed, created_at
    FROM agent_run WHERE application_id = $1
    ORDER BY created_at
  `, [id]);

  return { app, materials, agentRuns };
}

export async function getWeeklyInsights(): Promise<WeeklyInsightRow[]> {
  const { rows } = await pool.query<WeeklyInsightRow>(`
    SELECT id, week_start, insights, generated_at
    FROM weekly_insight
    ORDER BY week_start DESC
  `);
  return rows;
}

export async function getResumeEntries(): Promise<MasterResumeEntry[]> {
  const { rows } = await pool.query<MasterResumeEntry>(`
    SELECT id, category, canonical_text, facts, tags, priority
    FROM master_resume_entry
    ORDER BY
      CASE category
        WHEN 'education'    THEN 1
        WHEN 'experience'   THEN 2
        WHEN 'project'      THEN 3
        WHEN 'skill'        THEN 4
        WHEN 'achievement'  THEN 5
        ELSE 6
      END,
      COALESCE(priority, 0) DESC
  `);
  return rows;
}

export async function getResumeEntry(id: string): Promise<MasterResumeEntry | null> {
  const { rows } = await pool.query<MasterResumeEntry>(
    `SELECT id, category, canonical_text, facts, tags, priority
     FROM master_resume_entry WHERE id = $1`,
    [id]
  );
  return rows[0] ?? null;
}

export async function getUserProfile(): Promise<UserProfile | null> {
  const { rows } = await pool.query<UserProfile>(
    `SELECT id, name, email, phone, location, linkedin_url, github_url, long_term_goals, target_role_types, updated_at FROM user_profile LIMIT 1`
  );
  return rows[0] ?? null;
}
