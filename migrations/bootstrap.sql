CREATE SCHEMA IF NOT EXISTS mlspend;
-- statement boundary
CREATE TABLE IF NOT EXISTS mlspend.mlspend_request_log (
  id VARCHAR PRIMARY KEY, kind VARCHAR NOT NULL, created_at VARCHAR NOT NULL,
  payload VARCHAR NOT NULL, result VARCHAR NOT NULL, period VARCHAR,
  scored_at VARCHAR, actual_micro BIGINT
);
-- statement boundary
CREATE INDEX IF NOT EXISTS ix_mlspend_kind ON mlspend.mlspend_request_log(kind);
-- statement boundary
CREATE INDEX IF NOT EXISTS ix_mlspend_period ON mlspend.mlspend_request_log(period);
-- statement boundary
CREATE TABLE IF NOT EXISTS mlspend.mlspend_client_budget (
  client_hash VARCHAR NOT NULL, "window" INTEGER NOT NULL, count INTEGER NOT NULL,
  PRIMARY KEY(client_hash,"window")
);
-- statement boundary
DO $$ BEGIN
  IF to_regclass('public.mlspend_request_log') IS NOT NULL THEN
    INSERT INTO mlspend.mlspend_request_log SELECT * FROM public.mlspend_request_log ON CONFLICT DO NOTHING;
  END IF;
  IF to_regclass('public.mlspend_client_budget') IS NOT NULL THEN
    INSERT INTO mlspend.mlspend_client_budget SELECT * FROM public.mlspend_client_budget ON CONFLICT DO NOTHING;
  END IF;
END $$;
