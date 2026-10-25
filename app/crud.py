from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URL
from app.utils import generate_code


class AliasTakenError(Exception):
    pass


def get_by_code(db: Session, code: str) -> URL | None:
    return db.scalar(select(URL).where(URL.code == code))


def _try_insert(db: Session, code: str, target_url: str) -> URL | None:
    """Insert a row; return None if the code already exists."""
    url = URL(code=code, target_url=target_url)
    db.add(url)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(url)
    return url


def create_url(db: Session, target_url: str, code_length: int,
               alias: str | None = None, max_attempts: int = 5) -> URL:
    if alias is not None:
        url = _try_insert(db, alias, target_url)
        if url is None:
            raise AliasTakenError(alias)
        return url

    for _ in range(max_attempts):
        url = _try_insert(db, generate_code(code_length), target_url)
        if url is not None:
            return url
    raise RuntimeError("Could not generate a unique code")


def increment_clicks(db: Session, url_id: int) -> None:
    # Atomic SQL update: clicks = clicks + 1.
    db.execute(
        update(URL).where(URL.id == url_id).values(clicks=URL.clicks + 1)
    )
    db.commit()
