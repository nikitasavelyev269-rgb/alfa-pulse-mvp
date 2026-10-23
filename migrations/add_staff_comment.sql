-- Run once against the existing ALFA PULSE PostgreSQL database.
-- Safe to re-run: it does not delete or modify existing application rows.
ALTER TABLE applications
ADD COLUMN IF NOT EXISTS staff_comment TEXT;
