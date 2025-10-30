# Notes Database API

This folder contains the SQLite database and a Flask REST API exposing CRUD endpoints for the simple notes app.

## Prerequisites

- Python 3.9+ recommended
- SQLite (lib available with Python's sqlite3 module)
- pip

## Setup

1) Install dependencies:

```bash
cd simple-notes-app-182240-182249/notes_database
pip install -r requirements.txt
```

2) Initialize the database (creates myapp.db and notes table if not present):

```bash
python3 init_db.py
```

3) Start the API server:

```bash
PORT=5001 DB_PATH=./myapp.db python3 api_server.py
```

- The server listens on `0.0.0.0` on port `5001` by default.
- CORS is enabled for `http://localhost:3000` so the React app can call this API.

## Environment Variables

You may configure the server with a `.env` file in this directory or via environment variables:

- `PORT`: Port for the Flask server (default `5001`)
- `DB_PATH`: Path to the SQLite database file (default `./myapp.db`)

Example `.env`:

```
PORT=5001
DB_PATH=./myapp.db
```

## API Endpoints

- `GET /api/notes` — list all notes
- `GET /api/notes/<id>` — get a single note by id
- `POST /api/notes` — create a note; JSON body: `{ "title": "string", "content": "string" }`
- `PUT /api/notes/<id>` — update a note; JSON body: `{ "title": "string?", "content": "string?" }` (at least one required)
- `DELETE /api/notes/<id>` — delete a note

Health:
- `GET /api/health` — server and DB presence info

## Notes

- The existing database file is `myapp.db`. By default, the API uses it.
- If you change `DB_PATH` in `.env`, ensure it points to a valid SQLite file or run `init_db.py` accordingly.
