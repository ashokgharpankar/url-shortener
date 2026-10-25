from datetime import datetime

from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    target_url: HttpUrl  # rejects "not a url" with a 422 automatically


class URLInfo(BaseModel):
    code: str
    target_url: str
    short_url: str
    clicks: int
    created_at: datetime
