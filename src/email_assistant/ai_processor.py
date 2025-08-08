"""
AI处理模块
"""

from typing import List, Optional
from sentence_transformers import SentenceTransformer
import jieba
import re
from .main import DB_FILE
import sqlite3

class AIProcessor:
    """AI处理类"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # 初始化模型
        self.model = SentenceTransformer(model_name)
    
    def generate_summary(self, texts: List[str], max_length: int = 300) -> str:
        """生成文本摘要"""
        # 合并所有文本
        combined_text = " ".join(texts)
        
        # 简单的摘要方法：提取前几句话
        # 在实际应用中，可以使用更复杂的摘要算法
        sentences = re.split(r'[。！？.!?]', combined_text)
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence + "。"
            else:
                break
        
        return summary.strip()
    
    def extract_tasks(self, text: str) -> List[str]:
        """从文本中提取任务"""
        tasks = []
        
        # 使用正则表达式匹配常见的任务关键词
        task_patterns = [
            r'(?:(?:需要|请|要|应该|必须|务必|得).*?)(?:完成|做|处理|执行|实施|开展|进行|推进|落实)',
            r'(?:任务|工作|事项).*?(?:：|:)',
            r'(?:待办|TODO|To-do).*?(?:：|:)',
            r'- \[ \] .*',  # Markdown未完成任务项
        ]
        
        for pattern in task_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tasks.extend(matches)
        
        # 使用jieba分词进行更智能的识别
        words = jieba.lcut(text)
        task_indicators = ['任务', '工作', '待办', '计划', '安排']
        for i, word in enumerate(words):
            if word in task_indicators and i < len(words) - 1:
                # 简单的任务提取逻辑
                task = word + words[i+1] if i+1 < len(words) else word
                tasks.append(task)
        
        # 去重并清理
        tasks = list(set(tasks))
        tasks = [task.strip(' -[]') for task in tasks if len(task.strip()) > 2]
        
        return tasks
    
    def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def search_similar_emails(self, query: str, folder: Optional[str] = None, top_k: int = 5) -> List[dict]:
        """搜索相似邮件"""
        # 生成查询向量
        query_embedding = self.generate_embedding(query)
        
        # 连接数据库
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 构建查询语句
        if folder:
            cursor.execute('''
                SELECT e.id, e.subject, e.sender, e.date, e.content, 
                       distance(email_vectors.embedding, ?) as similarity
                FROM emails e
                JOIN email_vectors ON e.id = email_vectors.email_id
                WHERE e.folder = ?
                ORDER BY similarity
                LIMIT ?
            ''', (str(query_embedding), folder, top_k))
        else:
            cursor.execute('''
                SELECT e.id, e.subject, e.sender, e.date, e.content, 
                       distance(email_vectors.embedding, ?) as similarity
                FROM emails e
                JOIN email_vectors ON e.id = email_vectors.email_id
                ORDER BY similarity
                LIMIT ?
            ''', (str(query_embedding), top_k))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "subject": row[1],
                "sender": row[2],
                "date": row[3],
                "content": row[4],
                "similarity": row[5]
            })
        
        conn.close()
        return results