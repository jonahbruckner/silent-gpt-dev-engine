from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class RawQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str
    source_id: str
    title: str
    body: str
    tags: str
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="new")  # new | processed | rejected


class ContentItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_id: Optional[int] = Field(default=None, foreign_key="rawquestion.id")
    type: str  # tutorial | cheatsheet | snippet_pack
    title: str
    body_md: str
    tags: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="draft")  # draft | reviewed | published
