#!/usr/bin/env python3
"""Test SQLite database connection and notes table basic CRUD"""

import sqlite3
import sys
import os
import time

DB_NAME = "myapp.db"

try:
    # Check if database file exists
    if not os.path.exists(DB_NAME):
        print(f"Database file '{DB_NAME}' not found")
        sys.exit(1)

    # Connect to database and get version
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sqlite_version()")
    version = cursor.fetchone()[0]

    # Verify notes table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
    if not cursor.fetchone():
        print("Notes table does not exist. Please run init_db.py first.")
        conn.close()
        sys.exit(1)

    # Insert a sample note (use a unique title to avoid conflicts)
    title = f"Sample Note {int(time.time())}"
    content = "Hello from test_db.py"
    cursor.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (title, content)
    )
    note_id = cursor.lastrowid

    # Read it back
    cursor.execute("SELECT id, title, content FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()

    # Clean up the inserted row to keep environment tidy (optional)
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()

    conn.close()

    if not row:
        print("Failed to insert/select from notes table")
        sys.exit(1)

    print(f"SQLite version: {version}")
    print("Notes table sanity check: insert/select/delete OK")
    sys.exit(0)

except sqlite3.Error as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
