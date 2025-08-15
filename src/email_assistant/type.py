# 定义数据模型
from datetime import datetime
from typing import List
from pydantic import BaseModel


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

class DailySummary(BaseModel):
    date: str
    summary: str
    tasks: List[str]