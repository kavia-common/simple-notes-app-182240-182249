#!/usr/bin/env python3
"""Initialize SQLite database for notes_database.

This script is idempotent and can be safely re-run. It ensures the required schema
for the simple notes app exists, including a 'notes' table.
"""

import sqlite3
import os

DB_NAME = "myapp.db"
DB_USER = "kaviasqlite"  # Not used for SQLite, but kept for consistency
DB_PASSWORD = "kaviadefaultpassword"  # Not used for SQLite, but kept for consistency
DB_PORT = "5000"  # Not used for SQLite, but kept for consistency

print("Starting SQLite setup...")

# Check if database already exists
db_exists = os.path.exists(DB_NAME)
if db_exists:
    print(f"SQLite database already exists at {DB_NAME}")
    # Verify it's accessible
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("SELECT 1")
        conn.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print("Creating new SQLite database...")

# Create or open database and ensure schema
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Ensure foreign keys are enabled (good practice for SQLite)
cursor.execute("PRAGMA foreign_keys = ON")

# Create initial meta tables (kept from template for utility/diagnostics)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Notes table required by the simple notes app
# Fields:
# - id: primary key autoincrement
# - title: required text
# - content: required text
# - created_at: default now
# - updated_at: default now (application should update this on changes)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Optional sample users table retained from initial scaffold (harmless, idempotent)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Insert/Update app_info rows idempotently
cursor.execute("INSERT OR REPLACE INTO app_info (id, key, value, created_at) VALUES ((SELECT id FROM app_info WHERE key=?), ?, ?, COALESCE((SELECT created_at FROM app_info WHERE key=?), CURRENT_TIMESTAMP))",
               ("project_name", "project_name", "notes_database", "project_name"))
cursor.execute("INSERT OR REPLACE INTO app_info (id, key, value, created_at) VALUES ((SELECT id FROM app_info WHERE key=?), ?, ?, COALESCE((SELECT created_at FROM app_info WHERE key=?), CURRENT_TIMESTAMP))",
               ("version", "version", "0.2.0", "version"))
cursor.execute("INSERT OR REPLACE INTO app_info (id, key, value, created_at) VALUES ((SELECT id FROM app_info WHERE key=?), ?, ?, COALESCE((SELECT created_at FROM app_info WHERE key=?), CURRENT_TIMESTAMP))",
               ("author", "author", "John Doe", "author"))
cursor.execute("INSERT OR REPLACE INTO app_info (id, key, value, created_at) VALUES ((SELECT id FROM app_info WHERE key=?), ?, ?, COALESCE((SELECT created_at FROM app_info WHERE key=?), CURRENT_TIMESTAMP))",
               ("description", "description", "", "description"))

conn.commit()

# Get database statistics (including notes table presence)
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
table_count = cursor.fetchone()[0]

# Count app_info rows
cursor.execute("SELECT COUNT(*) FROM app_info")
record_count = cursor.fetchone()[0]

# Verify notes table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
notes_exists = cursor.fetchone() is not None

conn.close()

# Save connection information to a file
current_dir = os.getcwd()
connection_string = f"sqlite:///{current_dir}/{DB_NAME}"

try:
    with open("db_connection.txt", "w") as f:
        f.write(f"# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {current_dir}/{DB_NAME}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
db_path = os.path.abspath(DB_NAME)

# Ensure db_visualizer directory exists
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w") as f:
        f.write(f"export SQLITE_DB=\"{db_path}\"\n")
    print(f"Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nSQLite setup complete!")
print(f"Database: {DB_NAME}")
print(f"Location: {current_dir}/{DB_NAME}")
print("")
print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")

print("\nTo connect to the database, use one of the following methods:")
print(f"1. Python: sqlite3.connect('{DB_NAME}')")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {current_dir}/{DB_NAME}")
print("")

print("Database statistics:")
print(f"  Tables: {table_count}")
print(f"  App info records: {record_count}")
print(f"  Notes table present: {'yes' if notes_exists else 'no'}")

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess
    result = subprocess.run(['which', 'sqlite3'], capture_output=True, text=True)
    if result.returncode == 0:
        print("")
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {DB_NAME}")
except:
    pass

# Exit successfully
print("\nScript completed successfully.")
