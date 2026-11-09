-- Add provenance fields required by the protected remote-image ingestion route.
-- Safe to apply repeatedly; existing textbook-image rows remain unchanged.
ALTER TABLE lesson_image_assets
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS source_page_url TEXT,
    ADD COLUMN IF NOT EXISTS license_name TEXT,
    ADD COLUMN IF NOT EXISTS license_url TEXT,
    ADD COLUMN IF NOT EXISTS creator TEXT,
    ADD COLUMN IF NOT EXISTS attribution TEXT;
