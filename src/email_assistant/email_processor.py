"""
邮件处理模块
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict
from datetime import datetime
import sqlite3
from .main import Email, DB_FILE

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
    
    def fetch_emails(self, folder: str = "INBOX", days: int = 1) -> List[Email]:
        """获取指定文件夹中的邮件"""
        if not self.client:
            raise Exception("未连接到邮件服务器")
        
        # 选择文件夹
        self.client.select(folder)
        
        # 计算日期范围
        date = datetime.now().strftime("%d-%b-%Y")
        search_criteria = f'(SINCE {date})'
        
        # 搜索邮件
        status, messages = self.client.search(None, search_criteria)
        if status != 'OK':
            raise Exception("搜索邮件失败")
        
        email_ids = messages[0].split()
        emails = []
        
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
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')
                
                # 获取发件人和收件人
                sender = msg.get("From", "")
                recipient = msg.get("To", "")
                
                # 获取日期
                date_str = msg.get("Date", "")
                
                # 获取邮件正文
                content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            charset = part.get_content_charset()
                            if charset:
                                content = part.get_payload(decode=True).decode(  # pyright: ignore[reportAttributeAccessIssue]
                                    charset if charset else 'utf-8', 
                                    errors='ignore'
                                )
                            break
                else:
                    charset = msg.get_content_charset()
                    if charset:
                        content = msg.get_payload(decode=True).decode(  # pyright: ignore[reportAttributeAccessIssue]
                            charset if charset else 'utf-8', 
                            errors='ignore'
                        )
                
                # 创建邮件对象
                email_obj = Email(
                    subject=subject,
                    sender=sender,
                    recipient=recipient,
                    date=date_str,
                    content=content,
                    folder=folder
                )
                
                emails.append(email_obj)
            except Exception as e:
                print(f"解析邮件失败 (ID: {email_id.decode()}): {str(e)}")
                continue
        
        return emails

def save_emails_to_db(emails: List[Email]):
    """保存邮件到数据库"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for email_obj in emails:
            cursor.execute('''
                INSERT OR REPLACE INTO emails (subject, sender, recipient, date, content, folder)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email_obj.subject,
                email_obj.sender,
                email_obj.recipient,
                email_obj.date,
                email_obj.content,
                email_obj.folder
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"保存邮件到数据库失败: {str(e)}")
        return False