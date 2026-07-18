-- MboaShield tenant RLS activation template.
-- This script is fail-closed: it refuses to enable RLS until every protected
-- table has a populated tenant_id column. It is not applied to the SQLite demo.
--
-- The application must set the tenant for every database transaction:
--   SET LOCAL app.tenant_id = 'cm';

BEGIN;

DO $$
DECLARE
  target_table text;
BEGIN
  FOREACH target_table IN ARRAY ARRAY[
    'incident_reports',
    'verification_checks',
    'trust_assessments',
    'shared_alerts'
  ]
  LOOP
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.columns AS c
      WHERE c.table_schema = 'public'
        AND c.table_name = target_table
        AND c.column_name = 'tenant_id'
    ) THEN
      RAISE EXCEPTION
        'RLS activation refused: %.tenant_id does not exist. Add and backfill it first.',
        target_table;
    END IF;
  END LOOP;
END
$$;

ALTER TABLE incident_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE trust_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE shared_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mboashield_tenant_incidents ON incident_reports;
CREATE POLICY mboashield_tenant_incidents ON incident_reports
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS mboashield_tenant_checks ON verification_checks;
CREATE POLICY mboashield_tenant_checks ON verification_checks
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS mboashield_tenant_assessments ON trust_assessments;
CREATE POLICY mboashield_tenant_assessments ON trust_assessments
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS mboashield_tenant_alerts ON shared_alerts;
CREATE POLICY mboashield_tenant_alerts ON shared_alerts
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

COMMIT;
