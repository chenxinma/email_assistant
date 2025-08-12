"""
邮件助手主应用模块
"""


from contextlib import asynccontextmanager
import sqlite3
from turtle import title
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, Request
from openai import AsyncOpenAI
import sqlite_vec
from tqdm.asyncio import tqdm

from email_assistant.email_processor import EmailClient, save_emails_to_db

from .config import ConfigManager
from .type import *


# 配置文件路径
CONFIG_FILE = "data/config.json"

# 数据库文件路径
DB_FILE = "data/email_assistant.db"

# 初始化数据库
def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    
    # 创建邮件表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER UNIQUE,
            subject TEXT,
            sender TEXT,
            recipient TEXT,
            date DATETIME,
            content TEXT,
            folder TEXT
        )
    ''')
    
    # 创建向量表
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS email_vectors 
        USING vec0(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            embedding FLOAT[1024]  -- 使用bge-large-zh-v1.5模型的维度
        )
    ''')
    
    # 创建模板表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            subject TEXT,
            content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

async def fetch_emails():
    """从邮箱获取邮件"""
    
    config_manager = ConfigManager(CONFIG_FILE)
    host = config_manager.config["mail"]["imapServer"]
    port = config_manager.config["mail"]["imapPort"]
    username = config_manager.config["mail"]["emailAddress"]
    password = config_manager.config["mail"]["emailPassword"]
    embedding_model = AsyncOpenAI(
                        api_key="cannot be empty",
                        base_url=config_manager.config["ai"]["embeddingBaseUrl"])
    embedding_model_id = config_manager.config["ai"]["embeddingModel"]

    email_client = EmailClient(host, port, username, password)
    async def get_embedding(text: str) -> List[float]:
        embeding = await embedding_model.embeddings.create(input=text, model=embedding_model_id)
        return embeding.data[0].embedding
    
    if email_client.connect():
        conn = sqlite3.connect(DB_FILE)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)

        emails = email_client.fetch_emails()
        async for email in tqdm(emails, desc="处理邮件"):
            await save_emails_to_db(email, conn, get_embedding)
        conn.commit()
        conn.close()
    return {"message": "邮件刷新成功"}

# 应用生命周期管理
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 应用启动时初始化
    config_manager = ConfigManager(CONFIG_FILE)
    config_manager.load_config()
    init_database()
    yield {
        "config": config_manager.config
    }

async def get_config_inject(request: Request) -> Dict[str, Any]:
    return request.state.config

# 创建FastAPI应用
app = FastAPI(
    title="邮件助手API",
    description="智能邮件管理、摘要生成和知识库系统",
    version="0.1.0",
    lifespan=lifespan
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

from fastapi.responses import StreamingResponse
import json

@app.post("/api/emails/refresh")
async def refresh_emails(days: int = 1, config: Dict[str, Any] = Depends(get_config_inject)):
    """刷新邮件"""
    host = config["mail"]["imapServer"]
    port = config["mail"]["imapPort"]
    username = config["mail"]["emailAddress"]
    password = config["mail"]["emailPassword"]
    embedding_model = AsyncOpenAI(
                        api_key="cannot be empty",
                        base_url=config["ai"]["embeddingBaseUrl"])
    embedding_model_id = config["ai"]["embeddingModel"]
    print(embedding_model_id)

    async def get_embedding(text: str) -> List[float]:
        embeding = await embedding_model.embeddings.create(input=text, model=embedding_model_id)
        return embeding.data[0].embedding

    async def generate_stream():
        email_client = EmailClient(host, port, username, password)
        if email_client.connect():
            conn = sqlite3.connect(DB_FILE)
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)

            emails = email_client.fetch_emails(days=days)
            n_cnt = 0
            e_cnt = 0
            async for email in emails:
                result = await save_emails_to_db(email, conn, get_embedding)
                if result:
                    n_cnt += 1
                    yield f'data: {json.dumps({"message": "邮件处理中", "count": n_cnt, "title": email.subject})}\n\n'
                else:
                    e_cnt += 1
                    yield f'data: {json.dumps({"message": "邮件处理失败", "count": n_cnt, "title": email.subject})}\n\n'
            
            conn.commit()
            conn.close()
            yield f'data: {json.dumps({"message": "邮件刷新成功", "count": n_cnt})}\n\n'
        else:
            yield f'data: {json.dumps({"message": "连接邮件服务器失败"})}\n\n'
        yield 'data: [DONE]\n\n'

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@app.get("/api/emails")
async def get_emails(folder: str = "", limit: int = 10, offset: int = 0):
    """获取邮件列表"""
    try:
        conn = sqlite3.connect(DB_FILE)
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
async def search_emails(query: SearchQuery):
    """语义搜索邮件"""
    # 这里需要实现实际的搜索逻辑
    # 目前返回一个示例响应
    return {
        "query": query.query,
        "results": [
            {
                "id": 1,
                "subject": "示例邮件主题",
                "sender": "example@example.com",
                "date": "2025-08-08",
                "content": "这是一封示例邮件的内容",
                "similarity": 0.95
            }
        ]
    }

@app.get("/api/summary/daily")
async def get_daily_summary():
    """获取当日邮件摘要"""
    # 这里需要实现实际的摘要生成逻辑
    # 目前返回一个示例响应
    return {
        "date": "2025-08-08",
        "summary": "今天收到了10封邮件，主要涉及项目进展和会议安排。",
        "tasks": [
            "完成项目报告",
            "参加下午3点的团队会议",
            "回复客户邮件"
        ]
    }

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