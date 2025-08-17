"""
AI处理模块
"""
import datetime
import json
import re
import sqlite3
import textwrap
from typing import List, Optional, Union

import jieba
from openai import AsyncOpenAI
from pydantic_ai import Agent
from sqlite_vec import serialize_float32

from .models import qwen
from .type import DailyMailSummary


class AIProcessor:
    """AI处理类"""
    
    def __init__(self, embedding_base_url:str, embedding_model: str = "bge-large-zh-v1.5"):
        # 初始化模型
        self.embedding_model = AsyncOpenAI(
                        api_key="cannot be empty",
                        base_url=embedding_base_url)
        self.embedding_model_id = embedding_model
        # 初始化摘要生成agent
        self.summary_agent = Agent(
            qwen("qwen-turbo"),  # 使用较小的模型以节省成本
            output_type=DailyMailSummary,
            instructions=textwrap.dedent("""
            你是一个专业的邮件摘要生成器。
            你的任务是根据提供的邮件内容生成简洁、准确的摘要，突出关键信息和待办事项。

            - 输出的摘要文本采用Markdown格式。
            - 对于收件对象不是涉及你的邮件，只要简单描述一下，不要详细展开，不要生成代办事项。
            - 对于收件对象是涉及你的邮件，要详细展开，包括要关注的时间、待任务等。
            """)
        )

    def _make_mail_summary_prompt(self, whoami:str, summary: Optional[DailyMailSummary], email_info_list: List[dict])->str:
        return textwrap.dedent(
                        f"""你是{whoami}，基于以下邮件内容生成摘要，重点与你有关的关键信息和待办事项。
                        以下是已经摘录的邮件摘要和代办事项:
                        {summary.model_dump_json() if isinstance(summary, DailyMailSummary) else ''}
                        需要根据以上摘要和代办事项，继续摘录新的邮件内容。
                        新的邮件内容:
                        {json.dumps(email_info_list, ensure_ascii=False)}
                        """)


    async def generate_summary(self, date: datetime.date, whoami:str, conn: sqlite3.Connection) -> Union[DailyMailSummary, str]:

        """生成日期摘要"""
        # 连接数据库
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询指定日期的邮件属性数据
        cursor.execute(
            """
            SELECT 
                emails.uid, 
                email_attributes.recipient, 
                email_attributes.datetime,
                email_attributes.content
            FROM emails
            INNER JOIN email_attributes
            ON emails.uid = email_attributes.uid
            WHERE emails.date between date(?) and date(?, '+1 day')
            """,
            [date.isoformat(), date.isoformat()]
        )
        
        rows = cursor.fetchall()
        if not rows:
            return f"{date.strftime('%Y-%m-%d')} 没有找到邮件内容"

        # 初始化摘要内容
        char_count = 0
        email_info_list = []
        summary = None
        
        # 逐条处理邮件内容，控制每次传递给agent的内容小于1000字符
        for row in rows:
            recipient = row['recipient'] or ''
            content = row['content'] or ''
            attention_datetime = row['datetime'] or ''
            
            # 构造邮件信息
            email_info = textwrap.dedent(
                f"""- 收件人: {recipient}
                      要关注的时间: {attention_datetime}
                      内容: {content}
                """)
            
            # 如果当前摘要加上新邮件信息超过1000字符，或者这是第一条邮件，则生成摘要
            if char_count + len(email_info) > 1000:
                # 调用agent生成摘要
                result = await self.summary_agent.run(
                    self._make_mail_summary_prompt(whoami, summary, email_info_list))

                summary = result.output
                char_count = result.usage().response_tokens or 0

                email_info_list.clear()

            email_info_list.append(email_info)
            char_count += len(email_info)
            
        # 处理最后一批邮件内容
        if len(email_info_list) > 0:
            result = await self.summary_agent.run(
                self._make_mail_summary_prompt(whoami, summary, email_info_list))
            return result.output
        else:
            return f"{date.strftime('%Y-%m-%d')} 的邮件摘要生成失败"

    
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
