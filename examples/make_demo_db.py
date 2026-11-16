"""Create examples/demo.db, a tiny database to try the sqlite-readonly MCP server on."""
import sqlite3
from pathlib import Path

path = Path(__file__).with_name("demo.db")
path.unlink(missing_ok=True)
con = sqlite3.connect(path)
con.executescript("""
CREATE TABLE venues (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL);
CREATE TABLE nights (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id),
    weekday TEXT NOT NULL,
    signup TEXT NOT NULL,       -- 'door', 'book' or 'dm'
    last_verified TEXT          -- ISO date, NULL if never checked
);
INSERT INTO venues (name, city) VALUES
  ('The Tap Room', 'London'), ('Vinyl Bar', 'Bologna'), ('Circolo', 'Pisa');
INSERT INTO nights (venue_id, weekday, signup, last_verified) VALUES
  (1, 'Thursday', 'door', '2026-11-11'),
  (2, 'Friday',   'dm',   NULL),
  (3, 'Sunday',   'book', '2026-10-02');
""")
con.commit()
con.close()
print(f"wrote {path}")
