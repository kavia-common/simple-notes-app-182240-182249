# simple-notes-app-182240-182249

SQLite notes database setup

Schema (primary table):
- notes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

How to initialize:
- cd notes_database
- python3 init_db.py

Sanity test:
- python3 test_db.py
- Expected: prints SQLite version and confirms notes insert/select/delete is OK.
