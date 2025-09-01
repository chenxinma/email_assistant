"""
邮件助手主应用模块
"""
import os
from contextlib import asynccontextmanager
import json
import sqlite3
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite_vec

from .ai_processor import AIProcessor, AIProcessorException, AIProcessorNoDataException
from .config import ConfigManager
from .email_extract import extract_email_info
from .email_processor import EmailClient, EmailPresistence
from .type import *
from .log_config import setup_logging

logger = setup_logging(__name__)

# 配置文件路径
CONFIG_FILE = os.environ.get("CONFIG_FILE", "data/config.json")

# 数据库文件路径
DB_FILE = os.environ.get("DB_FILE", "data/email_assistant.db")

# 应用生命周期管理
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 应用启动时初始化
    config_manager = ConfigManager(CONFIG_FILE)
    config_manager.load_config()
    # 初始化数据库
    EmailPresistence.init_database(db_file=DB_FILE)
    # 初始化AI模型
    api_key = config_manager.config["ai"]["embeddingApiKey"]

    base_url = config_manager.config["ai"]["embeddingBaseUrl"]
    model_id = config_manager.config["ai"]["embeddingModel"]
    aiProcessor = AIProcessor(embedding_base_url=base_url,
                              embedding_model=model_id)
    emailPresistence = EmailPresistence(db_file=DB_FILE, 
                              embedding_base_url=base_url,
                              embedding_api_key=api_key,
                              embedding_model=model_id)
    yield {
        "config": config_manager.config,
        "aiProcessor": aiProcessor,
        "emailPresistence": emailPresistence,
    }

async def get_config_inject(request: Request) -> Dict[str, Any]:
    return request.state.config

async def get_ai_processor_inject(request: Request) -> AIProcessor:
    return request.state.aiProcessor

async def get_email_presistence_inject(request: Request) -> EmailPresistence:
    return request.state.emailPresistence

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

# 创建FastAPI应用
app = FastAPI(
    title="邮件助手API",
    description="智能邮件管理、摘要生成和知识库系统",
    version="0.1.0",
    lifespan=lifespan
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

# API路由
@app.get("/")
async def root():
    """根路径"""
    return {"message": "邮件助手API服务正在运行"}

@app.get("/api/config")
async def get_config(config: Dict[str, Any] = Depends(get_config_inject)):
    """获取配置"""
    return config



@app.post("/api/emails/refresh")
async def refresh_emails(days: int = 2, \
                         config: Dict[str, Any] = Depends(get_config_inject),
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
            attributes = extract_email_info(emailPresistence.get_noattribute_emails(), 'qwen3-coder-plus')
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


@app.get("/api/emails")
async def get_emails(folder: str = "", limit: int = 10, offset: int = 0):
    """获取邮件列表"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        if folder:
            cursor.execute('''
                SELECT id, subject, sender, recipient, date, content, folder
                FROM emails
                WHERE folder = ?
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            ''', (folder, limit, offset))
        else:
            cursor.execute('''
                SELECT id, subject, sender, recipient, date, content, folder
                FROM emails
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        emails = []
        for row in cursor.fetchall():
            emails.append({
                "id": row[0],
                "subject": row[1],
                "sender": row[2],
                "recipient": row[3],
                "date": row[4],
                "content": row[5],
                "folder": row[6]
            })
        
        conn.close()
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取邮件失败: {str(e)}")


@app.post("/api/emails/search")
async def search_emails(query: SearchQuery, aiProcessor: AIProcessor = Depends(get_ai_processor_inject)):
    """语义搜索邮件"""
    conn = get_conn()
    try:
        results = await aiProcessor.search_similar_emails(query.query, conn=conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索邮件失败: {str(e)}")
    finally:
        conn.close()
    return {
        "query": query.query,
        "results": results
    }

@app.get("/api/summary/daily")
async def get_daily_summary(
    config: Dict[str, Any] = Depends(get_config_inject),
    aiProcessor: AIProcessor = Depends(get_ai_processor_inject)):
    """获取当日邮件摘要"""
    conn = get_conn()
    whoami= config["ai"]["whoami"]
    today = datetime.today().date()
    try:
        summary = await aiProcessor.generate_summary(today, whoami, conn=conn)

        return {
            "date": today.strftime("%Y-%m-%d"),
            "summary": summary
        }
    except AIProcessorNoDataException as e:
        raise HTTPException(status_code=404, detail=e.message_text)
    except AIProcessorException as e:
        raise HTTPException(status_code=500, detail=e.message_text)


@app.get("/api/templates")
async def get_templates():
    """获取邮件模板列表"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, subject, content
            FROM templates
        ''')
        
        templates = []
        for row in cursor.fetchall():
            templates.append({
                "id": row[0],
                "name": row[1],
                "subject": row[2],
                "content": row[3]
            })
        
        conn.close()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")

@app.post("/api/templates")
async def create_template(template: Template):
    """创建邮件模板"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO templates (name, subject, content)
            VALUES (?, ?, ?)
        ''', (template.name, template.subject, template.content))
        
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": template_id, "message": "模板创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")

@app.post("/api/emails/send")
async def send_email(email: Email):
    """发送邮件"""
    # 这里需要实现实际的邮件发送逻辑
    # 目前只是返回一个示例响应
    return {"message": f"邮件 '{email.subject}' 发送成功"}

def run():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)