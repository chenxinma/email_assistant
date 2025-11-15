from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
import json
import os
import sqlite3
import textwrap
from typing import Any, List

from ag_ui.core import RunAgentInput
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
import logfire
from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent, RunContext
from pydantic_ai.ag_ui import SSE_CONTENT_TYPE, run_ag_ui
import sqlite_vec

from .ai_processor import AIProcessor, AIProcessorNoDataException
from .config import ConfigManager
from .email_extract import extract_email_info
from .email_processor import EmailClient, EmailPresistence
from .models import qwen
from .react.prompt import set_run_agent_input

# 配置文件路径
CONFIG_FILE = os.environ.get("CONFIG_FILE", "data/config.json")
# 数据库文件路径
DB_FILE = os.environ.get("DB_FILE", "data/email_assistant.db")

# 初始化
config_manager = ConfigManager(CONFIG_FILE)
config_manager.load_config()
# 从配置文件中获取OTEL_ENDPOINT
otel_endpoint = config_manager.get("otel_endpoint", None)
if otel_endpoint:
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'  
    logfire.configure(send_to_logfire=False, console=False, service_name="email-assistant")  
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
else:
    logfire.configure(send_to_logfire=False)  
    logfire.instrument_pydantic_ai(event_mode="logs")  

@dataclass
class Deps:
    aiProcessor: AIProcessor
    conn: sqlite3.Connection
    whoami: str

class EmailAttribute(BaseModel):
    subject: str
    sender: str
    date: str
    content: str

agent = Agent(
            qwen("qwen3-coder-plus"), 
            deps_type=Deps,
            instructions=textwrap.dedent("Be fun!")
        )

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

@agent.tool_plain
def current_date() -> str:
    """
    返回当前日期
    Returns:
        str: 当前日期，格式为YYYY-MM-DD
    """
    return datetime.now().strftime('%Y-%m-%d')

@agent.tool
async def search_emails(context: RunContext[Deps], query: str, limit: int = 3) -> List[EmailAttribute]:
    """
    搜索邮件
    Args:
        query (str): 搜索关键词
        limit (int, optional): 返回的邮件数量. Defaults to 3.
    Returns:
        str: 搜索结果
    """
    
    results = []
    try:
        with logfire.span('search emails'):
            results = await context.deps.aiProcessor.search_similar_emails(
                query, conn=context.deps.conn, top_k=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索邮件失败: {str(e)}")

    return [EmailAttribute(subject=email['subject'], 
                           sender=email['sender'], 
                           date=email['date'], 
                           content=email['content']) for email in results]

@agent.tool
async def summarize_daily_emails(context: RunContext[Deps], date:str) -> str:
    """
    对指定日期的邮件进行总结
    Args:
        date (str): 日期，格式为YYYY-MM-DD
    Returns:
        str: 总结
    """
    if not date:
        return "没有日期可总结"
    
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    whoami= context.deps.whoami
    try:
        with logfire.span('summarize_daily_emails, date={d}', d=date):
            return await context.deps.aiProcessor.generate_summary(target_date, whoami, context.deps.conn)
    except AIProcessorNoDataException as e:
        return f"{date}没有邮件"

@agent.tool
async def summarize_today_emails(context: RunContext[Deps]) -> str:
    """
    对今天的邮件进行总结
    
    Returns:
        str: 总结
    """
    
    target_date = datetime.now().date()
    return await summarize_daily_emails(context, target_date.strftime('%Y-%m-%d'))


# 应用生命周期管理
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 应用启动时初始化
    config_manager = ConfigManager(CONFIG_FILE)
    config_manager.load_config()
    # 初始化AI模型
    api_key = config_manager.config["ai"]["embeddingApiKey"]
    base_url = config_manager.config["ai"]["embeddingBaseUrl"]
    model_id = config_manager.config["ai"]["embeddingModel"]
    summary_model = config_manager.config["ai"]["summaryModel"]
    qa_model = config_manager.config["ai"]["qaModel"]

    aiProcessor = AIProcessor(embedding_base_url=base_url,
                              embedding_api_key=api_key,
                              embedding_model=model_id,
                              summary_model=summary_model,
                              qa_model=qa_model)
    emailPresistence = EmailPresistence(db_file=DB_FILE, 
                              embedding_base_url=base_url,
                              embedding_api_key=api_key,
                              embedding_model=model_id)
    yield {
        "aiProcessor": aiProcessor,
        "config": config_manager.config,
        "emailPresistence": emailPresistence,
    }

async def get_ai_processor_inject(request: Request) -> AIProcessor:
    return request.state.aiProcessor

async def get_config_inject(request: Request) -> dict[str, Any]:
    return request.state.config

async def get_email_presistence_inject(request: Request) -> EmailPresistence:
    return request.state.emailPresistence

app = FastAPI(
    version="0.1.0",
    title="邮件助手API",
    description="智能邮件管理、摘要生成和知识库系统",
    lifespan=lifespan,
)

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/emails/refresh")
async def refresh_emails(days: int = 2, \
                         config: dict[str, Any] = Depends(get_config_inject),
                         emailPresistence: EmailPresistence = Depends(get_email_presistence_inject)):
    """刷新邮件"""
    host = config["mail"]["imapServer"]
    port = config["mail"]["imapPort"]
    username = config["mail"]["emailAddress"]
    password = config["mail"]["emailPassword"]
 
    async def generate_stream():
        with logfire.span('refresh emails'):
            email_client = EmailClient(host, port, username, password)
            if email_client.connect():
                for folder in config["mail"]["indexedFolders"]:
                    emailPresistence.connect()
                    yield f'data: {json.dumps({"message": f"文件夹处理中 {folder}"})}\n\n'
                    last_uid = emailPresistence.get_last_uid(folder)
                    logfire.info("最后一个UID: {uid=}", uid=last_uid)
                    emails = email_client.fetch_emails(folder=folder, days=days, last_uid=last_uid)
                    n_cnt = 0
                    e_cnt = 0
                    async for email in emails:
                        result = await emailPresistence.save_emails_to_db(email)
                        if result:
                            n_cnt += 1
                            yield f'data: {json.dumps({"message": "邮件处理中", "count": n_cnt, "title": email.subject})}\n\n'
                        else:
                            e_cnt += 1
                            yield f'data: {json.dumps({"message": "邮件处理失败", "count": n_cnt, "title": email.subject})}\n\n'
                        logfire.info("处理完成，共 {n_cnt=} 条邮件，{e_cnt=} 条异常，当前UID: {uid=}", 
                                     n_cnt=n_cnt, e_cnt=e_cnt, uid=email.uid)
                        emailPresistence.commit()
                    
                    n_cnt = 0
                    e_cnt = 0
                    attributes = extract_email_info(emailPresistence.get_noattribute_emails())
                    for attr in attributes:
                        if emailPresistence.save_email_attributes_to_db(attr):
                            n_cnt += 1
                            yield f'data: {json.dumps({"message": "邮件属性保存中", "count": n_cnt, "title": attr.content[:20]})}\n\n'
                        else:
                            e_cnt += 1
                            yield f'data: {json.dumps({"message": "邮件属性保存失败", "count": n_cnt, "title": attr.content[:20]})}\n\n'
                        logfire.info("邮件属性提取，共 {n_cnt=} 条邮件，{e_cnt=} 条异常，当前UID: {uid=}", 
                                      n_cnt=n_cnt, e_cnt=e_cnt, uid=attr.uid)
                        emailPresistence.commit()
                    emailPresistence.close()
                    yield f'data: {json.dumps({"message": "邮件刷新成功", "count": n_cnt})}\n\n'
                else:
                    yield f'data: {json.dumps({"message": "连接邮件服务器失败"})}\n\n'
                    emailPresistence.close()
                yield 'data: [DONE]\n\n'

    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.post('/')
async def run_agent(request: Request, 
                    aiProcessor: AIProcessor = Depends(get_ai_processor_inject), 
                    config: dict[str, Any] = Depends(get_config_inject)) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = RunAgentInput.model_validate(await request.json())
        set_run_agent_input(run_input)
    except ValidationError as e:  # pragma: no cover
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    
    event_stream = run_ag_ui(agent, 
        run_input, 
        accept=accept, 
        deps=Deps(
            aiProcessor=aiProcessor, 
            whoami=config["ai"]["whoami"],
            conn=get_conn()))

    return StreamingResponse(event_stream, media_type=accept)

def run():
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=9000)
