from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URL
from app.utils import generate_code


def get_by_code(db: Session, code: str) -> URL | None:
    return db.scalar(select(URL).where(URL.code == code))


def create_url(db: Session, target_url: str, code_length: int,
               max_attempts: int = 5) -> URL:
    # Insert and let the unique constraint catch collisions. Checking
    # "does this code exist?" first would be a race condition.
    for _ in range(max_attempts):
        url = URL(code=generate_code(code_length), target_url=target_url)
        db.add(url)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(url)
        return url
    raise RuntimeError("Could not generate a unique code")


def increment_clicks(db: Session, url_id: int) -> None:
    # Atomic SQL update: clicks = clicks + 1. Reading the value,
    # adding 1 in Python and saving would lose clicks under load.
    db.execute(
        update(URL).where(URL.id == url_id).values(clicks=URL.clicks + 1)
    )
    db.commit()
