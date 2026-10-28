-- Rooms are private links. No names, audio or transcripts are ever stored.
CREATE TABLE IF NOT EXISTS rooms (
  id          text PRIMARY KEY,
  created_at  timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS rooms_expires_at_idx ON rooms (expires_at);

-- A seat is held by one browser (random identity) speaking one language.
-- Max two seats per room; a seat frees itself when its holder is not
-- connected to LiveKit and the seat is older than the reservation window.
CREATE TABLE IF NOT EXISTS room_seats (
  room_id     text NOT NULL REFERENCES rooms (id) ON DELETE CASCADE,
  identity    text NOT NULL,
  lang        text NOT NULL CHECK (lang IN ('te', 'hi', 'en', 'zh')),
  issued_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (room_id, identity)
);
