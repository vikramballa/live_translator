-- Rejoining a seat needs a secret (its SHA-256 is stored here), not the identity:
-- identities are visible to the other participant in LiveKit.
ALTER TABLE room_seats ADD COLUMN IF NOT EXISTS key_hash text;
