# schemas.py

from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from typing import Optional


# ── INCOMING REQUEST ──────────────────────────────────────────
# What the user sends us when they want to shorten a URL

class URLCreate(BaseModel):
    """
    Shape of the request body when creating a short URL.

    Example JSON the user sends:
    {
        "original_url": "https://www.example.com/very/long/path",
        "custom_code": "my-link"   ← optional!
    }
    """
    original_url: HttpUrl               # HttpUrl validates it's a real URL format
    custom_code: Optional[str] = None   # Optional custom alias (e.g., "my-blog")

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v):
        """Make sure custom codes are simple alphanumeric strings."""
        if v is not None:
            # Strip whitespace
            v = v.strip()
            if len(v) < 3:
                raise ValueError("Custom code must be at least 3 characters")
            if len(v) > 20:
                raise ValueError("Custom code must be 20 characters or less")
            if not v.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Custom code can only contain letters, numbers, hyphens, underscores")
        return v


# ── OUTGOING RESPONSE ─────────────────────────────────────────
# What we send back to the user after shortening

class URLResponse(BaseModel):
    """
    Shape of the response when a URL is successfully shortened.

    Example JSON we return:
    {
        "short_code": "abc123",
        "short_url": "http://localhost:8000/abc123",
        "original_url": "https://www.example.com/very/long/path",
        "click_count": 0,
        "created_at": "2024-01-15T10:30:00"
    }
    """
    short_code: str
    short_url: str          # the full clickable short URL
    original_url: str
    click_count: int
    created_at: datetime

    # This tells Pydantic to read data from SQLAlchemy model attributes
    # (not just plain dictionaries) — needed to convert DB rows → JSON
    model_config = {"from_attributes": True}


# ── STATS RESPONSE ────────────────────────────────────────────
# What we return when someone checks a link's analytics

class URLStats(BaseModel):
    """
    Shape of the analytics response.
    """
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
