# utils.py
# ─────────────────────────────────────────────────────────────
# Helper functions for the URL shortener.
#
# CONCEPT: How does URL shortening actually work?
#
# Option A — Hash the URL (e.g., MD5/SHA256)
#   Take the URL, run it through a hash function, use the first
#   6 chars. Problem: same URL always gives same hash, and
#   different URLs can sometimes give the same hash (collision).
#
# Option B — Random code (what we use) ✓
#   Pick 6 random characters from [a-z, A-Z, 0-9].
#   That gives us 62^6 = ~56 BILLION possible combinations.
#   We check the database to ensure no duplicates.
#
# Option C — Auto-increment ID encoded in base62
#   Use the database row ID (1, 2, 3...) and encode it.
#   Predictable but simpler. Used by early bit.ly.
#
# We're using Option B — random codes are unpredictable
# (good for privacy) and practically collision-free.
# ─────────────────────────────────────────────────────────────

import random
import string


# The "alphabet" our short codes are made from.
# 62 characters: a-z (26) + A-Z (26) + 0-9 (10)
ALPHABET = string.ascii_letters + string.digits  # "abcdefghijklmnopqrstuvwxyzABCDEF...0123456789"

# Length of the short code — 6 chars gives 56 billion combinations
CODE_LENGTH = 6


def generate_short_code(length: int = CODE_LENGTH) -> str:
    """
    Generate a random alphanumeric short code.

    Example outputs: "aB3xKq", "9mNpRz", "TuV4wX"

    How it works:
    - random.choices() picks `length` random items from ALPHABET
    - It allows repeats (so "aaaaaa" is technically possible, just rare)
    - "".join() combines the list of chars into a single string
    """
    return "".join(random.choices(ALPHABET, k=length))


def generate_unique_code(db, length: int = CODE_LENGTH) -> str:
    """
    Generate a short code that doesn't already exist in the database.

    Why loop?
    In theory, two different requests could generate the same random code.
    This function keeps trying until it finds one that's not taken.

    With 56 billion possibilities and a small database, this almost
    never needs more than one try — but it's good defensive coding!

    Args:
        db: the database session (to check for existing codes)
        length: how long the code should be

    Returns:
        A unique short code string
    """
    from models import URL  # imported here to avoid circular imports

    while True:
        code = generate_short_code(length)
        # Check if this code already exists in the database
        existing = db.query(URL).filter(URL.short_code == code).first()
        if not existing:
            return code  # found a unique one — return it!
        # If it exists, the while loop tries again automatically
