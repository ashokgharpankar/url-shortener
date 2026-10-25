from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

RESERVED_ALIASES = {"docs", "redoc", "stats", "shorten"}


class URLCreate(BaseModel):
    target_url: HttpUrl
    alias: str | None = Field(
        default=None,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    @field_validator("alias")
    @classmethod
    def alias_not_reserved(cls, v: str | None) -> str | None:
        if v is not None and v.lower() in RESERVED_ALIASES:
            raise ValueError("This alias is reserved")
        return v


class URLInfo(BaseModel):
    code: str
    target_url: str
    short_url: str
    clicks: int
    created_at: datetime
