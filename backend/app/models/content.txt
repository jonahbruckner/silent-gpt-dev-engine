from sqlmodel import SQLModel, Field
from typing import List, Optional
import datetime

class RawQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str
    source_id: str
    title: str
    body: str
    tags: str
    url: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    status: str = "new"  # new | processed | rejected

class ContentItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_id: Optional[int] = None
    type: str  # tutorial | cheatsheet | snippet_pack
    title: str
    body_md: str
    tags: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    status: str = "draft"  # draft | reviewed | published
