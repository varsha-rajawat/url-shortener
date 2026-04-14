# ⚡ Shortly — URL Shortener

A full-featured URL shortener built with **Python + FastAPI + SQLite**.
Built as a learning project — every file is heavily commented to explain concepts.

## Features
- Shorten any URL to a 6-character code
- Optional custom aliases (e.g. `/my-blog`)
- Click tracking & analytics
- Clean web UI + REST API
- Auto-generated API docs at `/docs`

## Project Structure

```
url-shortener/
├── main.py          ← FastAPI app: all routes & logic
├── database.py      ← SQLite connection via SQLAlchemy
├── models.py        ← Database table definition
├── schemas.py       ← Pydantic request/response shapes
├── utils.py         ← Short code generator
├── requirements.txt ← Python dependencies
└── static/
    └── index.html   ← Web UI frontend
```

## How to Run

### 1. Make sure Python 3.9+ is installed
```bash
python3 --version
```

### 2. Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the server
```bash
uvicorn main:app --reload
```

The `--reload` flag restarts the server automatically when you edit files.

### 5. Open in your browser
- **Web UI:** http://localhost:8000
- **API Docs (interactive!):** http://localhost:8000/docs
- **API Docs (alternative):** http://localhost:8000/redoc

## API Endpoints

| Method | Path                  | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | `/shorten`            | Create a short URL             |
| GET    | `/{short_code}`       | Redirect to original URL       |
| GET    | `/stats/{short_code}` | Get click stats for a URL      |
| GET    | `/api/urls`           | List all shortened URLs        |

### Example: Shorten a URL via curl
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.google.com"}'
```

### Example: Shorten with custom alias
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.github.com", "custom_code": "github"}'
```

## Architecture

```
Browser
   │
   ▼
FastAPI (main.py)
   │
   ├── POST /shorten   → validate URL → generate code → save to DB → return short URL
   ├── GET /{code}     → look up code in DB → increment clicks → 302 redirect
   ├── GET /stats/{code} → look up code → return click count + metadata
   └── GET /api/urls   → return all URLs (paginated)
   │
   ▼
SQLite (urls.db)   ← single file, auto-created on first run
```

## Key Concepts Covered
- **REST API design** — HTTP methods, status codes, routes
- **ORM** — SQLAlchemy models vs raw SQL
- **Data validation** — Pydantic schemas
- **Dependency injection** — FastAPI's `Depends()`
- **HTTP redirects** — 302 responses with Location header
- **Click tracking** — incrementing a counter on each visit
- **Frontend ↔ Backend** — Fetch API / AJAX calls

## Next Steps (to extend this project)
- Add user accounts & authentication (JWT tokens)
- Add URL expiration (delete links after N days)
- Add QR code generation
- Deploy to the cloud (Railway, Render, or Fly.io — all free tier)
- Switch to PostgreSQL for production
- Add rate limiting (prevent spam)
