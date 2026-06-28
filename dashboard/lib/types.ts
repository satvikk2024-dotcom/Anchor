export type ApplicationStatus =
  | "intake_received"
  | "researched"
  | "low_match_waiting"
  | "awaiting_review"
  | "submitted"
  | "responded"
  | "interview"
  | "rejected"
  | "ghosted"
  | "errored"
  | "withdrawn";

export interface ApplicationRow {
  id: string;
  url: string;
  company_id: string | null;
  company_name: string | null; // joined from company
  role_title: string | null;
  status: ApplicationStatus;
  match_score: number | null;
  created_at: string; // ISO timestamp
  submitted_at: string | null;
  responded_at: string | null;
  follow_up_window_days: number;
}

export interface AgentRunRow {
  id: string;
  application_id: string | null;
  company_name: string | null; // joined
  role_title: string | null; // joined
  workflow_name: string;
  agent_name: string;
  input_hash: string | null;
  output_json: unknown; // jsonb
  latency_ms: number | null;
  critic_passed: boolean | null;
  created_at: string;
}

export interface WeeklyInsightPattern {
  observation: string;
  evidence: string;
  suggested_action: string;
  confidence: "low" | "medium" | "high";
}

export interface WeeklyInsightRow {
  id: string;
  week_start: string; // date
  insights: {
    summary?: string;
    patterns?: WeeklyInsightPattern[];
  } | null;
  generated_at: string;
}

export type ResumeEntryCategory =
  | "education"
  | "experience"
  | "project"
  | "skill"
  | "achievement";

export interface MasterResumeEntry {
  id: string;
  category: ResumeEntryCategory;
  canonical_text: string;
  facts: Record<string, unknown> | null;
  tags: string[];
  priority: number | null;
}

export interface UserProfile {
  id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  long_term_goals: string | null;
  target_role_types: string[];
  updated_at: string;
}
