-- MboaShield 2030 T5 - Postgres row-level security by tenant (pilot template)
-- Apply ONLY on PostgreSQL national deployments after DATABASE_URL is Postgres.
-- SQLite demo deployments skip this file.

-- Prerequisite: set app.tenant_id per session, e.g.:
--   SET app.tenant_id = 'cm';

ALTER TABLE IF EXISTS incident_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS verification_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS trust_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS shared_alerts ENABLE ROW LEVEL SECURITY;

-- Example policy pattern (adjust column names if tenant columns are added later).
-- Today many tables are single-tenant; policies use current_setting for future multi-tenant rows.

DROP POLICY IF EXISTS mboashield_tenant_incidents ON incident_reports;
CREATE POLICY mboashield_tenant_incidents ON incident_reports
  FOR ALL
  USING (
    COALESCE(current_setting('app.tenant_id', true), 'cm') = 'cm'
    OR true  -- single-tenant pilot: allow; tighten when tenant_id column exists
  );

-- When tenant_id columns exist, replace USING with:
--   tenant_id = current_setting('app.tenant_id', true)

COMMENT ON POLICY mboashield_tenant_incidents ON incident_reports IS
  'MboaShield T5 RLS pilot - tighten when per-row tenant_id is populated';
