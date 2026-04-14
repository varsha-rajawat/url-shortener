# main.py
# ─────────────────────────────────────────────────────────────
# The main FastAPI application.
#
# CONCEPT: What is an API?
# API = Application Programming Interface.
# It's a set of rules for how programs talk to each other.
# A Web API is just a program that listens for HTTP requests
# and responds with data (usually JSON).
#
# CONCEPT: HTTP Methods
# When your browser visits a URL, it uses HTTP "methods":
#   GET    → "give me data"   (visiting a webpage, clicking a link)
#   POST   → "here's new data" (submitting a form)
#   DELETE → "remove this data"
#
# CONCEPT: Routes / Endpoints
# A "route" maps a URL path + HTTP method to a function.
# Example: GET /abc123 → run the redirect_to_url() function
#
# CONCEPT: HTTP Status Codes
# Every HTTP response has a numeric status:
#   200 = OK (success)
#   201 = Created (new resource made)
#   301/302 = Redirect (go here instead)
#   404 = Not Found
#   409 = Conflict (e.g., code already taken)
#   422 = Unprocessable Entity (bad input data)
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from utils import generate_unique_code

# ── App Setup ─────────────────────────────────────────────────

# Create all database tables defined in models.py
# If the tables already exist, this does nothing (safe to call on startup)
models.Base.metadata.create_all(bind=engine)

# Create the FastAPI application
# The metadata here powers the auto-generated docs at /docs
app = FastAPI(
    title="URL Shortener",
    description="A simple URL shortening service with click analytics",
    version="1.0.0"
)

# Serve files from the "static" folder at the root path
# This lets us serve our index.html frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Route 1: Homepage ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def homepage():
    """
    Serve the HTML frontend.

    When a user visits http://localhost:8000/ in their browser,
    they get back our index.html page.
    """
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())


# ── Route 2: Shorten a URL ────────────────────────────────────

@app.post("/shorten", response_model=schemas.URLResponse, status_code=201)
def shorten_url(
    url_data: schemas.URLCreate,   # Pydantic validates the request body automatically
    request: Request,              # FastAPI gives us the Request object (for building the short URL)
    db: Session = Depends(get_db)  # Dependency injection: give me a DB session
):
    """
    Create a shortened URL.

    FLOW:
    1. User sends POST /shorten with {"original_url": "https://..."}
    2. We validate the input (Pydantic handles this)
    3. If custom_code provided: check it's not taken
    4. Otherwise: generate a unique random code
    5. Save to database
    6. Return the short URL

    CONCEPT: Dependency Injection
    The `db: Session = Depends(get_db)` line is FastAPI's DI system.
    Instead of creating a DB session manually in every function,
    we declare "I need a db session" and FastAPI provides one.
    This also ensures the session is properly closed after each request.
    """

    # Convert Pydantic's HttpUrl object to a plain string for storage
    original_url_str = str(url_data.original_url)

    # Handle custom code or generate a random one
    if url_data.custom_code:
        # User wants a specific code — check if it's available
        existing = db.query(models.URL).filter(
            models.URL.short_code == url_data.custom_code
        ).first()

        if existing:
            # HTTP 409 Conflict — the code is already taken
            raise HTTPException(
                status_code=409,
                detail=f"The code '{url_data.custom_code}' is already taken. Try a different one."
            )
        short_code = url_data.custom_code
    else:
        # Auto-generate a unique code
        short_code = generate_unique_code(db)

    # Create a new URL record and save it to the database
    new_url = models.URL(
        original_url=original_url_str,
        short_code=short_code
    )
    db.add(new_url)      # stage the new record
    db.commit()          # write it to the database file
    db.refresh(new_url)  # reload from DB to get auto-set fields (id, created_at)

    # Build the full short URL (e.g., "http://localhost:8000/abc123")
    base_url = str(request.base_url).rstrip("/")
    short_url = f"{base_url}/{short_code}"

    # Return the response — FastAPI + Pydantic serialize this to JSON automatically
    return schemas.URLResponse(
        short_code=new_url.short_code,
        short_url=short_url,
        original_url=new_url.original_url,
        click_count=new_url.click_count,
        created_at=new_url.created_at
    )


# ── Route 3: Redirect ─────────────────────────────────────────

@app.get("/{short_code}")
def redirect_to_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    """
    Redirect a short code to the original URL.

    FLOW:
    1. User visits http://localhost:8000/abc123
    2. We look up "abc123" in the database
    3. If found: increment click count, redirect to original URL
    4. If not found: return 404

    CONCEPT: HTTP Redirect
    A redirect response doesn't send back a page — it sends
    back a status code (302) with a "Location" header pointing
    elsewhere. The browser then automatically navigates there.

    This is exactly how real URL shorteners work!
    bit.ly/xyz → 302 Found → Location: https://actual-site.com
    """

    # Look up the short code in the database
    url_record = db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()

    if not url_record:
        raise HTTPException(
            status_code=404,
            detail=f"Short URL '{short_code}' not found."
        )

    # Increment the click counter
    # This is how we track analytics!
    url_record.click_count += 1
    db.commit()

    # 302 = temporary redirect (browser won't cache it, good for counting clicks)
    return RedirectResponse(url=url_record.original_url, status_code=302)


# ── Route 4: Get Stats ────────────────────────────────────────

@app.get("/stats/{short_code}", response_model=schemas.URLStats)
def get_stats(
    short_code: str,
    db: Session = Depends(get_db)
):
    """
    Get analytics for a short URL.

    Returns: original URL, click count, creation date.

    Note: This route is defined BEFORE /{short_code} in the file,
    but we use the prefix "/stats/" to distinguish it from redirects.
    If we used "/info/{short_code}", FastAPI would try to redirect
    to a URL with code "info" instead!
    """

    url_record = db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()

    if not url_record:
        raise HTTPException(
            status_code=404,
            detail=f"Short URL '{short_code}' not found."
        )

    return url_record


# ── Route 5: List All URLs ────────────────────────────────────

@app.get("/api/urls", response_model=list[schemas.URLResponse])
def list_urls(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all shortened URLs (paginated).

    CONCEPT: Pagination
    Instead of returning ALL urls (could be millions!),
    we use skip + limit:
    - skip=0,  limit=20 → rows 1-20   (page 1)
    - skip=20, limit=20 → rows 21-40  (page 2)

    Query params go in the URL: /api/urls?skip=0&limit=20
    FastAPI reads them from the function signature automatically.
    """

    urls = db.query(models.URL).offset(skip).limit(limit).all()
    base_url = str(request.base_url).rstrip("/")

    return [
        schemas.URLResponse(
            short_code=url.short_code,
            short_url=f"{base_url}/{url.short_code}",
            original_url=url.original_url,
            click_count=url.click_count,
            created_at=url.created_at
        )
        for url in urls
    ]
