from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
import json
import os
import sqlite3
import textwrap
from typing import Any, List, Optional

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

from .email_extract import extract_email_info
from .email_processor import EmailClient, EmailPresistence
from .ai_processor import AIProcessor
from .config import ConfigManager
from .models import qwen

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
    logfire.configure(send_to_logfire=False, console=False, service_name="cli-agent")  
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)

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
            qwen("qwen-plus"), 
            deps_type=Deps,
            instructions=textwrap.dedent("""
            Be fun!
            你是一个专业的邮件问答助手。
            你的任务是根据提供的邮件内容回答用户的问题。
            - 答案采用Markdown格式，分段，调理清晰。
            - 当用户询问当前日期时，使用current_date工具获取当前日期。
            - 当用户问询问题时，邮件内容，使用search_emails工具回答用户。答案要简洁，不要超过500个字符。查询时，最多只展示前3封邮件的内容摘要。
            - 当用户指定日期的邮件总结时，使用summarize_daily_emails工具。根据提供的邮件内容生成简洁、准确的摘要，突出关键信息和待办事项。摘要输出文字数要小于800。把与你<User/>相关的内如放到前面，把与你<User/>无关的内如放到后面。
            
            ### 问询问题回答格式：
            {用户问题的总结回答}

            共搜索到{搜索到的邮件数}封相关的邮件，分别是：
            1. [subject1] 
                {邮件内容摘要1}

            2. [sunject2] 
                {邮件内容摘要2}

            ### 邮件总结示例：
            > 今日邮件摘要（2025年7月17日）

            ## 与我相关

            ** 工单处理 ** ：需处理工单 xxxxxx。
            **运维平台命名**：确认平台名称为 SyncoOps，已通知相关人员。

            ## 其他事项

            收到反垃圾邮件系统通知。
            """)
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
    return await context.deps.aiProcessor.generate_summary(target_date, whoami, context.deps.conn)

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

    aiProcessor = AIProcessor(embedding_base_url=base_url,
                              embedding_api_key=api_key,
                              embedding_model=model_id)
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
        email_client = EmailClient(host, port, username, password)
        if email_client.connect():
            emailPresistence.connect()
            last_uid = emailPresistence.get_last_uid()
            print(f"最后一个UID: {last_uid}")
            emails = email_client.fetch_emails(days=days, last_uid=last_uid)
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
                print(f"处理完成，共 {n_cnt} 条邮件，{e_cnt} 条异常，当前UID: {email.uid}", end="\r")
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
                print(f"邮件属性提取，共 {n_cnt} 条邮件，{e_cnt} 条异常，当前UID: {attr.uid}", end="\r")
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
    except ValidationError as e:  # pragma: no cover
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    event_stream = run_ag_ui(agent, run_input, accept=accept, deps=Deps(
        aiProcessor=aiProcessor, 
        whoami=config["ai"]["whoami"],
        conn=get_conn()))

    return StreamingResponse(event_stream, media_type=accept)

def run():
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=9000)
