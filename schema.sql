CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'gebruiker'
 CHECK(role IN ('gebruiker','admin'))
);
CREATE TABLE IF NOT EXISTS film (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 150),
 genre TEXT NOT NULL DEFAULT '', year INTEGER, description TEXT NOT NULL DEFAULT '',
 poster_url TEXT NOT NULL DEFAULT '', tmdb_id INTEGER,
 status TEXT NOT NULL DEFAULT 'beschikbaar' CHECK(status IN ('beschikbaar','uitgeleend','gereserveerd')),
 holder_id INTEGER REFERENCES users(id), deleted INTEGER NOT NULL DEFAULT 0 CHECK(deleted IN (0,1)),
 CHECK((status='beschikbaar' AND holder_id IS NULL) OR (status!='beschikbaar' AND holder_id IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS logging (
 id INTEGER PRIMARY KEY, film_id INTEGER NOT NULL REFERENCES film(id),
 user_id INTEGER NOT NULL REFERENCES users(id),
 action TEXT NOT NULL CHECK(action IN ('huren','terugbrengen','reserveren','annuleren')),
 timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_logging_user ON logging(user_id);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
