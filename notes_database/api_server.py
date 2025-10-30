#!/usr/bin/env python3
"""
Flask REST API server for Simple Notes App.

Provides CRUD endpoints for notes stored in a local SQLite database.

Environment variables:
- PORT: Port for the Flask server to listen on (default: 5001)
- DB_PATH: Path to the SQLite database file (default: ./myapp.db)

Endpoints:
/api/notes                [GET]    - List all notes
/api/notes/<int:id>       [GET]    - Get a single note by ID
/api/notes                [POST]   - Create a new note (JSON: {title, content})
/api/notes/<int:id>       [PUT]    - Update an existing note by ID (JSON: {title, content})
/api/notes/<int:id>       [DELETE] - Delete a note by ID

CORS:
- Allows requests from http://localhost:3000 (frontend)

Notes:
- Uses sqlite3 with row_factory for dict-like rows.
- Returns proper 404 when note not found.
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# Optional .env loading support without adding extra dependency:
# We will parse a simple KEY=VALUE format if a .env file exists.
def load_simple_env(env_path: str = ".env") -> None:
    """
    Load simple KEY=VALUE pairs from a .env file into process environment.

    Only loads lines of the form KEY=VALUE; ignores comments and empty lines.
    Quotes around values are stripped if present.
    """
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key:
                    os.environ.setdefault(key, value)
    except Exception:
        # Fail silently; environment variables can still be provided by the system
        pass

# Load .env (optional)
load_simple_env()

PORT = int(os.getenv("PORT", "5001"))
DB_PATH = os.getenv("DB_PATH", "./myapp.db")

app = Flask(
    __name__,
)
# Allow the React dev server
CORS(
    app,
    resources={r"/api/*": {"origins": ["http://localhost:3000"]}},
    supports_credentials=False,
)


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite connection with row factory as dict-like rows.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign keys and good defaults
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Convert sqlite3.Row to a plain dict.
    """
    return {k: row[k] for k in row.keys()}


def note_by_id(note_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single note by ID, or None if not found.
    """
    with get_connection() as conn:
        cur = conn.execute("SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?", (note_id,))
        row = cur.fetchone()
        return row_to_dict(row) if row else None


# PUBLIC_INTERFACE
@app.get("/api/notes")
def list_notes():
    """List all notes.

    Returns:
        JSON array of notes objects:
        [
            {
                "id": int,
                "title": str,
                "content": str,
                "created_at": str,
                "updated_at": str
            },
            ...
        ]
    """
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, title, content, created_at, updated_at FROM notes ORDER BY id DESC"
            )
            rows = cur.fetchall()
            return jsonify([row_to_dict(r) for r in rows])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# PUBLIC_INTERFACE
@app.get("/api/notes/<int:note_id>")
def get_note(note_id: int):
    """Get a single note by ID.

    Path params:
        note_id: integer ID of the note

    Returns:
        200 with note JSON if found
        404 if not found
    """
    try:
        note = note_by_id(note_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        return jsonify(note)
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


def validate_note_payload(data: Dict[str, Any], require_both: bool = True):
    """
    Validate note payload. Returns (ok: bool, message: Optional[str])

    Args:
        data: dict payload from request.json
        require_both: if True, require both title and content to be present;
                      if False, allow partial updates but require at least one.
    """
    if not isinstance(data, dict):
        return False, "Invalid JSON payload"
    title_present = "title" in data and isinstance(data["title"], str) and data["title"].strip() != ""
    content_present = "content" in data and isinstance(data["content"], str) and data["content"].strip() != ""

    if require_both:
        if not title_present or not content_present:
            return False, "Both 'title' and 'content' are required and must be non-empty strings"
        return True, None
    else:
        if not title_present and not content_present:
            return False, "At least one of 'title' or 'content' must be a non-empty string"
        return True, None


# PUBLIC_INTERFACE
@app.post("/api/notes")
def create_note():
    """Create a new note.

    Body (JSON):
        {
            "title": "string (required, non-empty)",
            "content": "string (required, non-empty)"
        }

    Returns:
        201 with created note JSON on success
        400 on validation error
    """
    data = request.get_json(silent=True) or {}
    ok, msg = validate_note_payload(data, require_both=True)
    if not ok:
        return jsonify({"error": msg}), 400

    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (data["title"].strip(), data["content"].strip()),
            )
            new_id = cur.lastrowid
            conn.commit()
            created = note_by_id(new_id)
            return jsonify(created), 201
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# PUBLIC_INTERFACE
@app.put("/api/notes/<int:note_id>")
def update_note(note_id: int):
    """Update an existing note.

    Path params:
        note_id: integer ID of note

    Body (JSON) - at least one field is required:
        {
            "title": "string (optional, non-empty)",
            "content": "string (optional, non-empty)"
        }

    Returns:
        200 with updated note JSON on success
        400 on validation error
        404 if note does not exist
    """
    # Check existence first
    existing = note_by_id(note_id)
    if not existing:
        return jsonify({"error": "Note not found"}), 404

    data = request.get_json(silent=True) or {}
    ok, msg = validate_note_payload(data, require_both=False)
    if not ok:
        return jsonify({"error": msg}), 400

    # Build dynamic update
    fields = []
    values = []
    if "title" in data and isinstance(data["title"], str) and data["title"].strip():
        fields.append("title = ?")
        values.append(data["title"].strip())
    if "content" in data and isinstance(data["content"], str) and data["content"].strip():
        fields.append("content = ?")
        values.append(data["content"].strip())

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    fields.append("updated_at = CURRENT_TIMESTAMP")
    try:
        with get_connection() as conn:
            query = f"UPDATE notes SET {', '.join(fields)} WHERE id = ?"
            values.append(note_id)
            conn.execute(query, tuple(values))
            conn.commit()
            updated = note_by_id(note_id)
            return jsonify(updated), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# PUBLIC_INTERFACE
@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id: int):
    """Delete a note by ID.

    Path params:
        note_id: integer ID of note

    Returns:
        204 on success when note existed and was deleted
        404 if note does not exist
    """
    # Check existence
    existing = note_by_id(note_id)
    if not existing:
        return jsonify({"error": "Note not found"}), 404

    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return ("", 204)
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# PUBLIC_INTERFACE
@app.get("/api/health")
def health():
    """Healthcheck endpoint.

    Returns:
        200 with basic status and database path information.
    """
    db_exists = os.path.exists(DB_PATH)
    return jsonify({
        "status": "ok",
        "db_path": os.path.abspath(DB_PATH),
        "db_exists": db_exists,
        "time": datetime.utcnow().isoformat() + "Z"
    })


def ensure_db_exists_hint():
    """
    Provide a helpful log if DB file is missing.
    """
    if not os.path.exists(DB_PATH):
        app.logger.warning(
            "SQLite database file not found at %s. Did you run 'python3 init_db.py'?",
            os.path.abspath(DB_PATH),
        )


if __name__ == "__main__":
    ensure_db_exists_hint()
    # Listen on all interfaces for containerized envs
    app.run(host="0.0.0.0", port=PORT, debug=False)
