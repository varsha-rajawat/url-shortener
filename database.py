# database.py
# ─────────────────────────────────────────────────────────────
# This file sets up the connection to our SQLite database.
#
# CONCEPT: SQLAlchemy ORM
# Instead of writing raw SQL like:
#   "SELECT * FROM urls WHERE short_code = 'abc123'"
# ...we use Python objects. SQLAlchemy translates for us.
#
# CONCEPT: SQLite
# The database is just a single file called "urls.db" that
# gets created automatically in your project folder.
# Perfect for development — no separate database server needed!
# ─────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# This is the connection string — it tells SQLAlchemy:
# - Use SQLite (not Postgres, MySQL, etc.)
# - Store the database in a file called "urls.db"
# - check_same_thread=False is needed for FastAPI's async nature
DATABASE_URL = "sqlite:///./urls.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# A "session" is like a temporary workspace for database operations.
# You open a session, do your reads/writes, then close it.
# Think of it like opening a file, editing it, then saving and closing.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our database models (tables) will inherit from.
class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────
# DEPENDENCY: get_db()
#
# In FastAPI, "dependencies" are functions that run before
# your route handler. This one gives each request its own
# fresh database session, and cleans it up when done.
#
# The "yield" keyword makes this a generator — code before
# yield runs first, then the route runs, then cleanup happens.
# ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db        # hand the session to the route
    finally:
        db.close()      # always close, even if an error occurred
