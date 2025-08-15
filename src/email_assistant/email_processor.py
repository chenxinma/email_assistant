"""
邮件处理模块
"""

from datetime import datetime, timedelta
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import imaplib
import sqlite3
import textwrap
from typing import AsyncGenerator, Awaitable, Callable, List, Optional, Tuple

from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from sqlite_vec import serialize_float32
import sqlite_vec

from .type import Email, EmailAttribute, EmailVector

class EmailClient:
    """邮件客户端"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
    
    def connect(self):
        """连接到邮件服务器"""
        try:
            self.client = imaplib.IMAP4_SSL(self.host, self.port)
            self.client.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"连接邮件服务器失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开邮件服务器连接"""
        if self.client:
            try:
                self.client.close()
                self.client.logout()
            except Exception as e:
                # 记录异常但不抛出，避免析构函数中出现错误
                print(f"断开邮件服务器连接时发生错误: {str(e)}")
            finally:
                # 确保将client设置为None，避免后续使用
                self.client = None
    
    def __del__(self):
        """析构函数，确保连接断开"""
        self.disconnect()
    
    def header_decode(self, encoded_header:str):
        if "=?" in encoded_header:
            decoded_headers = decode_header(encoded_header)
            decoded_texts = []
            for decoded_header in decoded_headers:
                decoded_text = decoded_header[0].decode(decoded_header[1] or 'utf-8')
                decoded_texts.append(decoded_text)

            return "".join(decoded_texts)
        else:
            return encoded_header
    
    def decode_text(self, text) -> Tuple[str, str]:
        """
        对邮件的主题或正文进行解码处理
        :param text: 待解码的文本
        :return: 解码后的文本
        """
        decoded_parts = decode_header(text)
        decoded_text:str = ""
        _encoding:str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    _encoding = encoding
                    decoded_text += part.decode(encoding, errors='ignore')
                else:
                    decoded_text += part.decode(errors='ignore')
            else:
                decoded_text += part
        return decoded_text, _encoding
    
    def get_email_content(self, msg):
        """
        根据邮件唯一标识符(UID)获取邮件内容。

        :param msg: 邮件消息对象
        :return: 邮件内容的字节流，如果获取失败则返回 None
        """
        # 获取邮件正文
        content = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    encoding = part.get_content_charset() or 'utf-8'
                    content = \
                        part.get_payload(decode=True).decode( # pyright:ignore 
                            encoding=encoding, errors='ignore') 
                    break
                elif part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode('utf-8') # pyright:ignore 
                    soup = BeautifulSoup(html, 'html.parser')
                    content = soup.get_text()
                elif part.get_content_type() in ["multipart/mixed", "multipart/related", "multipart/alternative"]:
                    continue
        else:
            encoding = msg.get_content_charset() or 'utf-8'
            content = \
                msg.get_payload(decode=True).decode( # pyright:ignore 
                    encoding=encoding, errors='ignore')
        if content.startswith("BEGIN:VCALENDAR"):
            return content
        else:
            dedented_text = textwrap.dedent(content).strip()
            # 移除 dedented_text 中的空白行
            lines = [line for line in dedented_text.splitlines() \
                        if line.strip() \
                            and not line.startswith('发件人：')
                            and not line.startswith('收件人：')
                            and not line.startswith('抄送：')]
            dedented_text = '\n'.join(lines)
            wrapped_text = textwrap.fill(dedented_text, width=100)
            wrapped_text = wrapped_text.replace(' _____ ', '\n_____\n')

            return wrapped_text
    
    async def fetch_emails(self, folder: str = "INBOX", days: int = 3, last_uid:int = 0) -> AsyncGenerator[Email, None]:
        """获取指定文件夹中的邮件"""
        if not self.client:
            raise Exception("未连接到邮件服务器")
        
        # 选择文件夹
        self.client.select(folder)
        
        # 计算日期范围
        # 注意：增量获取邮件是按照 最近3天（默认）的邮件进行查询，并获取的邮件UID > 最后已经存储的last_uid
        #       这样可能会存在使用间隔大于最近3天（默认）的邮件未能被获取的情况。
        date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')

        search_criteria = f'(SINCE {date})'
        status, messages = self.client.search(None, search_criteria)
        if status != 'OK':
            raise Exception("搜索邮件失败")

        email_ids = messages[0].split()
        if last_uid > 0:
            email_ids = [email_id for email_id in email_ids if int(email_id.decode('utf-8')) > last_uid]

        # 获取邮件内容
        for email_id in email_ids:
            try:
                # 获取邮件数据
                status, msg_data = self.client.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                # 检查是否有数据
                if not msg_data or not msg_data[0]:
                    continue
                
                # 解析邮件
                msg = email.message_from_bytes(msg_data[0][1])  # pyright: ignore[reportArgumentType]
                
                # 解码主题
                subject, encoding = self.decode_text(msg['subject'])
                
                # 获取发件人和收件人                
                sender = self.header_decode(msg.get("From", ""))
                recipient = self.header_decode(msg.get("To", ""))
                
                # 获取日期
                date_str = msg.get("Date", "")
                
                # 获取邮件正文
                content = self.get_email_content(msg)
                if len(content.strip()) == 0:
                    continue

                # 创建邮件对象
                email_obj = Email(
                    uid=email_id,
                    subject=subject,
                    sender=sender,
                    recipient=recipient,
                    date=parsedate_to_datetime(date_str),
                    content=content,
                    folder=folder
                )
                
                yield email_obj
            except Exception as e:
                print(f"解析邮件失败 (ID: {email_id.decode()}): {str(e)}")
                continue

class EmailPresistence:
    def __init__(self, db_file: str, 
                embedding_base_url:str, 
                embedding_model: str = "bge-large-zh-v1.5") -> None:
        self.db_file = db_file
        self.conn = None
        
        self.embedding_model = AsyncOpenAI(
                        api_key="cannot be empty",
                        base_url=embedding_base_url)
        self.embedding_model_id = embedding_model
    
    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_file)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    def __del__(self) -> None:
        if self.conn:
            self.conn.close()
    
    def commit(self) -> None:
        if self.conn:
            self.conn.commit()

    def get_last_uid(self, folder: str = "INBOX") -> int:
        """获取最后一个UID
        Args:
            conn: 数据库连接
            folder: 文件夹名称
        Return:
            int: 最后一个UID
        """
        if not self.conn:
            raise Exception("未连接到数据库")
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT max(uid) FROM emails WHERE folder = ?
            ''', (folder,))
            result = cursor.fetchone()
            if result:
                return int(result[0])
            else:
                return 0
        except Exception as e:
            print(f"获取最后一个UID失败: {str(e)}")
            return 0

    async def save_emails_to_db(self, email_obj: Email):
        """保存邮件到数据库
        Args:
            email_obj: 邮件对象
            conn: 数据库连接
            fn_embedding: 嵌入模型
        Return:
            bool: 是否成功
        """
        if not self.conn:
            raise Exception("未连接到数据库")
        try:
            cursor = self.conn.cursor()
        
            cursor.execute('''
                INSERT OR REPLACE INTO emails (uid, subject, sender, recipient, date, content, folder)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_obj.uid,
                email_obj.subject,
                email_obj.sender,
                email_obj.recipient,
                email_obj.date,
                email_obj.content,
                email_obj.folder
            ))
            # 将邮件内容按500字为一段进行分段
            content = f"{email_obj.subject}\n{email_obj.content}"
            lines = content.splitlines()
            # 每5行文本为一组，生成内容分段
            content_segments = []
            for i in range(0, len(lines), 5):
                segment = '\n'.join(lines[i:i+5])
                content_segments.append(segment)
            
            for _, segment in enumerate(content_segments):
                _embedding = await self.embedding_model.embeddings.create(
                    model=self.embedding_model_id,
                    input=segment
                )
                email_vector = EmailVector(
                    uid=email_obj.uid,
                    embedding=_embedding.data[0].embedding
                )
                cursor.execute('''
                        INSERT INTO email_vectors (uid, embedding)
                        VALUES (?, ?)
                    ''', (
                        email_vector.uid,
                        serialize_float32(email_vector.embedding)
                    ))
            
            return True
        except Exception as e:
            print(f"保存邮件到数据库失败: {str(e)}")
            return False

    def save_email_attributes_to_db(self, email_attr: EmailAttribute) -> bool:
        """保存邮件属性到数据库
        Args:
            email_attr: 邮件属性
            conn: 数据库连接
        Return:
            bool: 是否成功
        """
        if not self.conn:
            raise Exception("未连接到数据库")
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO email_attributes (uid, recipient, datetime, content)
                VALUES (?, ?, ?, ?)
            ''', (
                email_attr.uid,
                email_attr.recipient,
                email_attr.datetime,
                email_attr.content
            ))
            return True
        except Exception as e:
            print(f"保存邮件属性到数据库失败: {str(e)}")
            return False
    
    def get_email_by_uid(self, uid) -> Optional[Email]:
        """根据UID获取邮件
        Args:
            uid: 邮件UID
        Return:
            Email: 邮件对象
        """
        if not self.conn:
            raise Exception("未连接到数据库")
        
        cursor = self.conn.cursor()
        cursor.execute(textwrap.dedent(
            """SELECT 
                    uid,
                    subject, 
                    sender, 
                    content,
                    recipient,
                    \"date\",
                    folder
                FROM emails 
                WHERE uid = ?
            """), (uid,))
        row = cursor.fetchone()
        if row:
            email = Email(
                uid=row[0],
                subject=row[1],
                sender=row[2],
                content=row[3],
                recipient=row[4],
                date=row[5],
                folder=row[6]
            )
            return email
        else:
            return None
    
    def get_noattribute_emails(self) -> List[Email]:
        """获取没有属性的邮件
        Return:
            List[Email]: 邮件列表
        """
        if not self.conn:
            raise Exception("未连接到数据库")
        
        cursor = self.conn.cursor()
        cursor.execute(textwrap.dedent(
            """SELECT 
                    uid,
                    subject, 
                    sender, 
                    content,
                    \"date\"
                FROM emails 
                WHERE not exists (
                    select 1 from email_attributes where email_attributes.uid = emails.uid
                )
            """))
        result = cursor.fetchall()
        emails = []
        for row in result:
            email = Email(
                uid=row[0],
                subject=row[1],
                sender=row[2],
                content=row[3],
                recipient="",
                date=row[4],
                folder=""
            )
            emails.append(email)
        return emails


    # 初始化数据库
    @classmethod
    def init_database(cls, db_file: str):
        """初始化数据库"""
        conn = sqlite3.connect(db_file)
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

        # 创建邮件属性表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS email_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER UNIQUE,
                recipient TEXT,
                datetime DATETIME,
                content TEXT
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
