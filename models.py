# models.py
# ─────────────────────────────────────────────────────────────
# This file defines the shape of our data in the database.

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class URL(Base):
  
    __tablename__ = "urls"

    # Each Column() call creates one column in the table:

    # id: auto-incrementing number, the "primary key" (unique identifier for each row)
    # primary_key=True means SQLite will auto-assign 1, 2, 3... for each new URL
    id = Column(Integer, primary_key=True, index=True)

    # original_url: the full long URL the user submitted
    # nullable=False means this field is REQUIRED — can't be empty
    original_url = Column(String, nullable=False)

    # short_code: the 6-character random code we generate (e.g., "abc123")
    # unique=True means no two rows can have the same code — prevents collisions
    # index=True tells the database to create a fast-lookup index on this column
    #   (like a book's index — lets us find rows by short_code very quickly)
    short_code = Column(String, unique=True, index=True, nullable=False)

    # click_count: how many times this short link has been visited
    # default=0 means new URLs start with 0 clicks
    click_count = Column(Integer, default=0)

    # created_at: timestamp of when the URL was shortened
    # server_default=func.now() means the database sets this automatically
    #   to the current time when a new row is inserted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
