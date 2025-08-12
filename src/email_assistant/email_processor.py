"""
邮件处理模块
"""

from datetime import datetime, timedelta
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import imaplib
import sqlite3
from typing import AsyncGenerator, Awaitable, Callable, List, Tuple

from sqlite_vec import serialize_float32

from .type import Email, EmailVector

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
            self.client.close()
            self.client.logout()
    
    def __del__(self):
        """析构函数，确保连接断开"""
        self.disconnect()
    
    def header_decode(self, encoded_header:str):
        if encoded_header.startswith("=?"):
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
    
    async def fetch_emails(self, folder: str = "INBOX", days: int = 1) -> AsyncGenerator[Email, None]:
        """获取指定文件夹中的邮件"""
        if not self.client:
            raise Exception("未连接到邮件服务器")
        
        # 选择文件夹
        self.client.select(folder)
        
        # 计算日期范围
        date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
        search_criteria = f'(SINCE {date})'
        
        # 搜索邮件
        status, messages = self.client.search(None, search_criteria)
        if status != 'OK':
            raise Exception("搜索邮件失败")
        
        email_ids = messages[0].split()

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
                content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            encoding = part.get_content_charset() or 'utf-8'
                            content = \
                                part.get_payload(decode=True).decode( # pyright:ignore 
                                    encoding=encoding, errors='ignore') 
                            break
                else:
                    encoding = part.get_content_charset() or 'utf-8'
                    content = \
                        msg.get_payload(decode=True).decode( # pyright:ignore 
                            encoding=encoding, errors='ignore') 
                if len(content.strip()) == 0:
                    continue

                # 创建邮件对象
                email_obj = Email(
                    uid=email_id,
                    subject=subject,
                    sender=sender,
                    recipient=recipient,
                    date=parsedate_to_datetime(date_str),
                    content=content.strip(),
                    folder=folder
                )
                
                yield email_obj
            except Exception as e:
                print(f"解析邮件失败 (ID: {email_id.decode()}): {str(e)}")
                continue

async def save_emails_to_db(email_obj: Email,
                            conn: sqlite3.Connection,       
                            fn_embedding: Callable[[str], Awaitable[List[float]]]):
    """保存邮件到数据库
    Args:
        email_obj: 邮件对象
        conn: 数据库连接
        fn_embedding: 嵌入模型
    Return:
        bool: 是否成功
    """
    try:
        cursor = conn.cursor()
    
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
        content_segments = [content[i:i+500] for i in range(0, len(content), 500)]
        
        for _, segment in enumerate(content_segments):
            _embedding = await fn_embedding(segment)
            email_vector = EmailVector(
                uid=email_obj.uid,
                embedding=_embedding
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