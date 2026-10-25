from pathlib import Path

from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
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
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

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
    try:
        url = crud.create_url(
            db,
            str(payload.target_url),
            settings.code_length,
            alias=payload.alias,
        )
    except crud.AliasTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Alias already in use")
    return to_info(url)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/", response_class=HTMLResponse)
def home_submit(
    request: Request,
    target_url: str = Form(...),
    alias: str = Form(""),
    db: Session = Depends(get_db),
):
    context = {"target_url": target_url, "alias": alias}
    try:
        # Reuse the API's validation rules; an empty box means "no alias".
        payload = URLCreate(target_url=target_url, alias=alias or None)
        url = crud.create_url(db, str(payload.target_url),
                              settings.code_length, alias=payload.alias)
    except ValidationError as e:
        context["error"] = e.errors()[0]["msg"]
        return templates.TemplateResponse(request, "index.html", context,
                                          status_code=422)
    except crud.AliasTakenError:
        context["error"] = "That alias is already in use."
        return templates.TemplateResponse(request, "index.html", context,
                                          status_code=409)

    context["result"] = to_info(url)
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/{code}")
def follow(code: str, db: Session = Depends(get_db)):
    url = crud.get_by_code(db, code)
    if url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Short URL not found")
    crud.increment_clicks(db, url.id)
    return RedirectResponse(url.target_url,
                            status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/stats/{code}", response_model=URLInfo)
def stats(code: str, db: Session = Depends(get_db)):
    url = crud.get_by_code(db, code)
    if url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Short URL not found")
    return to_info(url)
