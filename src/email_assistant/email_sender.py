"""
邮件发送模块
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List

class EmailSender:
    """邮件发送类"""
    
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.server = None
    
    def connect(self):
        """连接到SMTP服务器"""
        try:
            if self.use_tls:
                self.server = smtplib.SMTP(self.host, self.port)
                self.server.starttls()
            else:
                self.server = smtplib.SMTP_SSL(self.host, self.port)
            
            self.server.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"连接SMTP服务器失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开SMTP服务器连接"""
        if self.server:
            self.server.quit()
    
    def send_email(self, sender: str, recipients: List[str], subject: str, content: str, content_type: str = "plain") -> bool:
        """发送邮件"""
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = Header(subject, 'utf-8')  # pyright: ignore[reportArgumentType]
            
            # 添加邮件正文
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            # 发送邮件
            self.server.send_message(msg)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False
    
    def send_html_email(self, sender: str, recipients: List[str], subject: str, html_content: str) -> bool:
        """发送HTML邮件"""
        return self.send_email(sender, recipients, subject, html_content, "html")