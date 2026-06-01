-- Run once on existing databases when upgrading list/pagination release.
-- New installs via create_all() already include these columns.
-- Idempotent: safe to run multiple times.

ALTER TABLE devices ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Single-column indexes (match Column(index=True) on the model)
CREATE INDEX IF NOT EXISTS ix_devices_department ON devices (department);
CREATE INDEX IF NOT EXISTS ix_devices_created_at ON devices (created_at);

-- Composite indexes (match Device.__table_args__)
CREATE INDEX IF NOT EXISTS ix_devices_status_created ON devices (status, created_at);
CREATE INDEX IF NOT EXISTS ix_devices_department_status ON devices (department, status);
CREATE INDEX IF NOT EXISTS ix_devices_owner_status ON devices (owner_id, status);
