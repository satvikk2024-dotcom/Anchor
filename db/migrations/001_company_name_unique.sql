-- Workflow 2 upserts company rows by name (domain is unfilled until website
-- research lands in Day 5), so we need a unique target for ON CONFLICT.
CREATE UNIQUE INDEX IF NOT EXISTS company_name_unique_idx ON company (lower(name));
