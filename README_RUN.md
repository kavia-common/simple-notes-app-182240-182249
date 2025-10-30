Backend quick run (Flask + SQLite)

cd notes_database
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
PORT=5001 DB_PATH=./myapp.db python3 api_server.py

API base: http://localhost:5001/api
CORS: allows http://localhost:3000
