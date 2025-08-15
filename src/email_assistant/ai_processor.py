"""
AI处理模块
"""
from typing import List, Optional
import jieba
import re

from openai import AsyncOpenAI
import sqlite3

from sqlite_vec import serialize_float32

class AIProcessor:
    """AI处理类"""
    
    def __init__(self, embedding_base_url:str, embedding_model: str = "bge-large-zh-v1.5"):
        # 初始化模型
        self.embedding_model = AsyncOpenAI(
                        api_key="cannot be empty",
                        base_url=embedding_base_url)
        self.embedding_model_id = embedding_model

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

    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        query_embedding = \
            await self.embedding_model.embeddings.create(input=text, 
                                                         model=self.embedding_model_id)
        return query_embedding.data[0].embedding
    
    async def search_similar_emails(self, query: str, conn:sqlite3.Connection, 
                                    folder: Optional[str] = None, top_k: int = 5) -> List[dict]:
        """搜索相似邮件"""
        # 生成查询向量
        query_embedding = await self.generate_embedding(query)
        
        # 连接数据库
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询语句
        if folder:
            cursor.execute(
                """
                SELECT
                    emails.uid,
                    emails.subject,
                    emails.sender,
                    emails.date,
                    emails.content,
                    vec.distance
                FROM
                    emails
                INNER JOIN (
                    SELECT 
                        uid,
                        min(distance) as distance
                    FROM (
                        SELECT
                            email_vectors.uid,
                            distance
                        FROM email_vectors
                        WHERE embedding MATCH ?
                            AND k = ?                    
                        ORDER BY distance
                    ) sub
                    GROUP BY uid
                ) vec ON emails.uid = vec.uid
                WHERE emails.folder = ?
                ORDER BY vec.distance ASC
                """,
                [serialize_float32(query_embedding), top_k, folder])
    
        else:
            cursor.execute(
                """
                SELECT
                    emails.uid,
                    emails.subject,
                    emails.sender,
                    emails.date,
                    emails.content,
                    vec.distance
                FROM
                    emails
                INNER JOIN (
                    SELECT 
                        uid,
                        min(distance) as distance
                    FROM (
                        SELECT
                            email_vectors.uid,
                            distance
                        FROM email_vectors
                        WHERE embedding MATCH ?
                            AND k = ?                    
                        ORDER BY distance
                    ) sub
                    GROUP BY uid
                ) vec ON emails.uid = vec.uid
                ORDER BY vec.distance ASC
                """,
                [serialize_float32(query_embedding), top_k])
        
        results = []
        for row in cursor.fetchall():
            results.append({k: row[k] for k in row.keys()})

        return results