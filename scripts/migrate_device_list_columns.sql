-- Run once on existing databases when upgrading list/pagination release.
-- New installs via create_all() already include these columns.

ALTER TABLE devices ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
CREATE INDEX IF NOT EXISTS ix_devices_department ON devices (department);
CREATE INDEX IF NOT EXISTS ix_devices_created_at ON devices (created_at);
