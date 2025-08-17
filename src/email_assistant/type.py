# 定义数据模型
from datetime import datetime
from typing import List
from typing_extensions import Annotated
from pydantic import BaseModel
from pydantic.fields import Field


class Email(BaseModel):
    id: int = 0
    uid: int
    subject: str
    sender: str
    recipient: str
    date: datetime
    content: str
    folder: str

class EmailVector(BaseModel):
    id: int = 0
    uid: int
    embedding: List[float]

class EmailAttribute(BaseModel):
    id: int = 0
    uid: int
    recipient: str = ""
    datetime: str = ""
    content: str = ""

class Template(BaseModel):
    id: int = 0
    name: str
    subject: str
    content: str

class SearchQuery(BaseModel):
    query: str
    folder: str = ""

class DailyMailSummary(BaseModel):
    summary: str
    tasks: List[str] = Field(default_factory=list, description="待办事项列表")

