"""
AI处理模块
"""
import datetime
import re
import sqlite3
import textwrap
from typing import List, Optional, Union

import cachetools
import jieba
from openai import AsyncOpenAI
from pydantic_ai import Agent
from sqlite_vec import serialize_float32

from .models import qwen
from .type import MailInfo, MailSummaryPrompt
import logging

summary_cache = cachetools.LRUCache(maxsize=100)

logger = logging.getLogger(__name__)

class AIProcessorException(Exception):
    """AI处理异常"""
    def __init__(self, message: str):
        super().__init__(message)


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
            qwen("qwen3-coder-flash"),  # 使用较小的模型以节省成本
            output_type=str,
            instructions=textwrap.dedent("""
            你是一个专业的邮件摘要生成器。
            你的任务是根据提供的邮件内容生成简洁、准确的摘要，突出关键信息和待办事项。
            
            - 输出的摘要文本采用Markdown格式。
            - 把与你<User/>相关的内如放到前面，把与你<User/>无关的内如放到后面。
            """)
        )

    def _make_mail_summary_prompt(self, whoami:str, summary: Optional[str], email_info_list: List[MailInfo])->str:
        prompt = MailSummaryPrompt(
            user=f"你是{whoami}",
            work_content="结合历史摘要<HistoryDailySummary/>和新的邮件内容<MailContents/>输出完整的摘要。注意不要丢失历史摘要的信息。",
            history_daily_summary=summary,
            mail_contents=email_info_list
        )
        prompt_str = prompt.to_xml(encoding='UTF-8',
                             standalone=True).decode('utf-8') # pyright: ignore[reportReturnType, reportAttributeAccessIssue]
        logger.info(prompt_str)
        return prompt_str

    async def generate_summary(self, date: datetime.date, whoami:str, conn: sqlite3.Connection) -> str:
        """生成日期摘要"""
        # 连接数据库
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        count = 0
        row = cursor.execute(
            """
            SELECT 
                count(1)
            FROM emails
            INNER JOIN email_attributes
            ON emails.uid = email_attributes.uid
            WHERE emails.date between date(?) and date(?, '+1 day')
            """,
            [date.isoformat(), date.isoformat()]
        ).fetchone()
        if row:
            count = row[0]
            if count == 0:
                raise AIProcessorException(f"{date.strftime('%Y-%m-%d')} 没有邮件内容")
            
        # 根据whoami count date 查询缓存
        key = f"{whoami}_{count}_{date.isoformat()}"
        if key in summary_cache:
            return summary_cache[key]

        # 查询指定日期的邮件属性数据
        cursor.execute(
            """
            SELECT 
                emails.uid, 
                email_attributes.recipient || ' ' || emails.recipient as recipient, 
                email_attributes.datetime,
                email_attributes.content
            FROM emails
            INNER JOIN email_attributes
            ON emails.uid = email_attributes.uid
            WHERE emails.date between date(?) and date(?, '+1 day')
            order by emails.uid
            """,
            [date.isoformat(), date.isoformat()]
        )
        
        rows = cursor.fetchall()
        if not rows:
            raise AIProcessorException(f"{date.strftime('%Y-%m-%d')} 没有邮件内容")

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
            email_info = MailInfo(
                recipient=recipient,
                attention_datetime=attention_datetime,
                content=content
            )
            mail_info_length = len(email_info.to_xml(encoding='UTF-8').decode('utf-8')) # pyright: ignore[reportAttributeAccessIssue]

            # 如果当前摘要加上新邮件信息超过2000字符，或者这是第一条邮件，则生成摘要
            if char_count + mail_info_length > 2000:
                # 调用agent生成摘要
                prompt = self._make_mail_summary_prompt(whoami, summary, email_info_list)
                result = await self.summary_agent.run(prompt)

                summary = result.output
                char_count = result.usage().response_tokens or 0

                email_info_list.clear()

            email_info_list.append(email_info)
            char_count += mail_info_length
            
        # 处理最后一批邮件内容
        if len(email_info_list) > 0:
            prompt = self._make_mail_summary_prompt(whoami, summary, email_info_list)
            result = await self.summary_agent.run(prompt)
            summary_cache[key] = result.output

            return result.output
        else:
            raise AIProcessorException(f"{date.strftime('%Y-%m-%d')} 的邮件摘要生成失败")

    
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
