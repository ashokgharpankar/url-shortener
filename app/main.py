from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import Base, engine, get_db
from app.models import URL
from app.schemas import URLCreate, URLInfo


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # fine for now; Alembic later
    yield


app = FastAPI(title="URL Shortener", lifespan=lifespan)


def to_info(url: URL) -> URLInfo:
    return URLInfo(
        code=url.code,
        target_url=url.target_url,
        short_url=f"{settings.base_url}/{url.code}",
        clicks=url.clicks,
        created_at=url.created_at,
    )


@app.post("/shorten", response_model=URLInfo,
          status_code=status.HTTP_201_CREATED)
def shorten(payload: URLCreate, db: Session = Depends(get_db)):
    url = crud.create_url(db, str(payload.target_url), settings.code_length)
    return to_info(url)


@app.get("/{code}")
def follow(code: str, db: Session = Depends(get_db)):
    url = crud.get_by_code(db, code)
    if url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Short URL not found")
    crud.increment_clicks(db, url.id)
    return RedirectResponse(url.target_url,
                            status_code=status.HTTP_307_TEMPORARY_REDIRECT)
