"""
邮件助手主应用模块
"""

import os
import json
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import sqlite_vec
from contextlib import asynccontextmanager

# 配置文件路径
CONFIG_FILE = "config.json"

# 数据库文件路径
DB_FILE = "email_assistant.db"

# 初始化配置
def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认配置
        config = {
            "mail": {
                "refreshInterval": 15,
                "indexedFolders": ["INBOX"]
            },
            "ai": {
                "model": "all-MiniLM-L6-v2",
                "summaryLength": 300
            }
        }
        # 保存默认配置
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return config

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
            subject TEXT,
            sender TEXT,
            recipient TEXT,
            date TEXT,
            content TEXT,
            folder TEXT
        )
    ''')
    
    # 创建向量表
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS email_vectors 
        USING vec0(
            email_id INTEGER,
            embedding FLOAT[384]  -- 使用all-MiniLM-L6-v2模型的维度
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

# 定义数据模型
class Email(BaseModel):
    id: int = 0
    subject: str
    sender: str
    recipient: str
    date: str
    content: str
    folder: str

class EmailVector(BaseModel):
    email_id: int
    embedding: List[float]

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

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时初始化
    load_config()
    init_database()
    yield
    # 应用关闭时清理资源（如果需要）

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
async def get_config():
    """获取配置"""
    return load_config()

@app.post("/api/emails")
async def add_email(email: Email):
    """添加邮件"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO emails (subject, sender, recipient, date, content, folder)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email.subject, email.sender, email.recipient, email.date, email.content, email.folder))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": email_id, "message": "邮件添加成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加邮件失败: {str(e)}")

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

@app.post("/api/emails/index")
async def index_email(email_vector: EmailVector):
    """为邮件创建向量索引"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_vectors (email_id, embedding)
            VALUES (?, ?)
        ''', (email_vector.email_id, json.dumps(email_vector.embedding)))
        
        conn.commit()
        conn.close()
        
        return {"message": "向量索引创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建向量索引失败: {str(e)}")

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

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)