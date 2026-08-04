"""
Shared Dependencies
=====================
Provides a DB session to route handlers and closes it afterwards.
"""


from database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()