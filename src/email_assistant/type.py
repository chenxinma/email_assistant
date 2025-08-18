# 定义数据模型
from datetime import datetime

from typing import List, Optional, Sequence
from pydantic import BaseModel
from pydantic_xml import BaseXmlModel, element, wrapped



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

class MailInfo(BaseXmlModel):
    recipient: str = element(tag="Recipient")
    attention_datetime: str = element(tag="AttentionDatetime")
    content: str = element(tag="Content")

class MailSummaryPrompt(BaseXmlModel):
    user: str = element(tag="User")
    work_content: str = element(tag="WorkContent")
    history_daily_summary: Optional[str] = element(tag="HistoryDailySummary")
    mail_contents: List[MailInfo] = wrapped(
        "MailContents",
        element(tag="Mail", default_factory=list)
    )



