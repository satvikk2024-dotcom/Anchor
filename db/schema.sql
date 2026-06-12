-- =====================================================================
-- Anchor — Postgres schema
-- Source of truth: docs/planning/anchor_planning.md §8.1
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------- Enum types ----------
CREATE TYPE application_status AS ENUM (
    'intake_received', 'researched', 'low_match_waiting', 'awaiting_review',
    'submitted', 'responded', 'interview', 'rejected', 'ghosted', 'errored', 'withdrawn'
);

CREATE TYPE resume_entry_category AS ENUM (
    'experience', 'project', 'skill', 'education', 'achievement'
);

CREATE TYPE generated_material_type AS ENUM (
    'tailored_resume', 'cover_letter', 'linkedin_message', 'skill_gap_report', 'follow_up_nudge'
);

-- ---------- company ----------
CREATE TABLE company (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                text NOT NULL,
    domain              text UNIQUE,
    synthesis           jsonb,
    last_researched_at  timestamptz
);

-- ---------- application ----------
CREATE TABLE application (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    url                     text NOT NULL,
    company_id              uuid REFERENCES company(id),
    role_title              text,
    status                  application_status NOT NULL DEFAULT 'intake_received',
    match_score             int CHECK (match_score BETWEEN 0 AND 100),
    created_at              timestamptz NOT NULL DEFAULT now(),
    submitted_at            timestamptz,
    responded_at            timestamptz,
    follow_up_window_days   int NOT NULL DEFAULT 10
);

-- ---------- master_resume_entry ----------
CREATE TABLE master_resume_entry (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category        resume_entry_category NOT NULL,
    canonical_text  text NOT NULL,
    facts           jsonb,
    tags            text[] NOT NULL DEFAULT '{}',
    priority        int CHECK (priority BETWEEN 1 AND 5)
);

-- ---------- generated_material ----------
CREATE TABLE generated_material (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      uuid NOT NULL REFERENCES application(id),
    type                generated_material_type NOT NULL,
    content_json        jsonb,
    content_rendered    text,
    pdf_drive_url       text,
    generated_at        timestamptz NOT NULL DEFAULT now(),
    model_used          text
);

-- ---------- material_grounding ----------
CREATE TABLE material_grounding (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id     uuid NOT NULL REFERENCES generated_material(id),
    master_entry_id uuid NOT NULL REFERENCES master_resume_entry(id),
    usage_note      text
);

-- ---------- agent_run ----------
CREATE TABLE agent_run (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid REFERENCES application(id),
    workflow_name   text NOT NULL,
    agent_name      text NOT NULL,
    input_hash      text,
    output_json     jsonb,
    latency_ms      int,
    critic_passed   boolean,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------- application_event ----------
CREATE TABLE application_event (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid REFERENCES application(id),
    event_type      text NOT NULL,
    payload         jsonb,
    occurred_at     timestamptz NOT NULL DEFAULT now()
);

-- ---------- weekly_insight ----------
CREATE TABLE weekly_insight (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start      date NOT NULL,
    insights        jsonb,
    generated_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------- user_profile ----------
CREATE TABLE user_profile (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    long_term_goals     text,
    target_role_types   text[] NOT NULL DEFAULT '{}',
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------- role_recommendation ----------
CREATE TABLE role_recommendation (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      uuid NOT NULL REFERENCES company(id),
    role_title      text NOT NULL,
    role_url        text,
    match_score     int CHECK (match_score BETWEEN 0 AND 100),
    rationale       text,
    top_gap         text,
    recommended     boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------- Indexes ----------
CREATE INDEX idx_application_status ON application(status);
CREATE INDEX idx_application_company_id ON application(company_id);
CREATE INDEX idx_generated_material_application_id ON generated_material(application_id);
CREATE INDEX idx_material_grounding_material_id ON material_grounding(material_id);
CREATE INDEX idx_agent_run_application_id ON agent_run(application_id);
CREATE INDEX idx_application_event_application_id ON application_event(application_id);
CREATE INDEX idx_role_recommendation_company_id ON role_recommendation(company_id);
