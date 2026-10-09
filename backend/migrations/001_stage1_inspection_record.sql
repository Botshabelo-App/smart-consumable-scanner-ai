-- Stage 1: full inspection record, audited corrections, sign-off, multi-inspection reports.
-- Additive and idempotent: safe to re-run; no existing data is deleted or overwritten.
-- Apply (after a pg_dump backup):
--   docker compose -f docker-compose.prod.yml exec -T db psql -U scanner -d consumable_scanner -v ON_ERROR_STOP=1 < backend/migrations/001_stage1_inspection_record.sql

ALTER TYPE review_status ADD VALUE IF NOT EXISTS 'ESCALATED';

BEGIN;

ALTER TABLE scans
    ADD COLUMN IF NOT EXISTS brand VARCHAR,
    ADD COLUMN IF NOT EXISTS packaging_condition VARCHAR,
    ADD COLUMN IF NOT EXISTS label_confidence DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS detected_fields TEXT,
    ADD COLUMN IF NOT EXISTS overall_result VARCHAR(32),
    ADD COLUMN IF NOT EXISTS overall_reason TEXT,
    ADD COLUMN IF NOT EXISTS ocr_raw_text TEXT,
    ADD COLUMN IF NOT EXISTS date_details TEXT,
    ADD COLUMN IF NOT EXISTS field_status TEXT,
    ADD COLUMN IF NOT EXISTS review_status VARCHAR(32),
    ADD COLUMN IF NOT EXISTS final_result VARCHAR(32),
    ADD COLUMN IF NOT EXISTS final_decision VARCHAR(32),
    ADD COLUMN IF NOT EXISTS signed_off_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS signed_off_by UUID REFERENCES users(id);

CREATE TABLE IF NOT EXISTS scan_corrections (
    id UUID PRIMARY KEY,
    scan_id UUID NOT NULL REFERENCES scans(id),
    user_id UUID NOT NULL REFERENCES users(id),
    field VARCHAR(64) NOT NULL,
    original_value TEXT,
    new_value TEXT,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_scan_corrections_scan_id ON scan_corrections (scan_id);

CREATE TABLE IF NOT EXISTS inspection_signoffs (
    id UUID PRIMARY KEY,
    scan_id UUID NOT NULL REFERENCES scans(id),
    user_id UUID NOT NULL REFERENCES users(id),
    full_name VARCHAR NOT NULL,
    typed_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    decision VARCHAR(32) NOT NULL,
    system_result VARCHAR(32),
    final_result VARCHAR(32),
    comments TEXT,
    override_reason TEXT,
    acknowledgement_text TEXT NOT NULL,
    created_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_inspection_signoffs_scan_id ON inspection_signoffs (scan_id);

ALTER TABLE reports
    ALTER COLUMN scan_id DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id),
    ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS report_type VARCHAR(16),
    ADD COLUMN IF NOT EXISTS format VARCHAR(8),
    ADD COLUMN IF NOT EXISTS filters TEXT;

CREATE INDEX IF NOT EXISTS ix_scans_company_created ON scans (company_id, created_at);

-- Backfill earlier scans from the "Overall result: X - reason" / "Brand detected:" finding lines.
UPDATE scans SET
    overall_result = replace(substring(findings from '^Overall result: ([A-Z ]+?) - '), ' ', '_'),
    overall_reason = substring(findings from '^Overall result: [A-Z ]+? - ([^\n]*)')
WHERE overall_result IS NULL AND findings LIKE 'Overall result: %';

UPDATE scans SET brand = substring(findings from 'Brand detected: ([^\n]*)')
WHERE brand IS NULL AND findings LIKE '%Brand detected: %';

UPDATE scans SET review_status = CASE WHEN overall_result = 'PASS_NO_VISIBLE_ANOMALY' THEN 'not_required' ELSE 'awaiting_review' END
WHERE review_status IS NULL;

UPDATE reports r SET company_id = s.company_id, report_type = 'single'
FROM scans s WHERE r.scan_id = s.id AND r.company_id IS NULL;

COMMIT;
