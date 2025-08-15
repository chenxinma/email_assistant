import email
import imaplib
import textwrap
import unittest

from bs4 import BeautifulSoup

from email_assistant.config import ConfigManager

class TestEmailFetch(unittest.TestCase):
    def setUp(self):
        config = ConfigManager("data/config.json")
        host = config.get('mail.imapServer', '')
        port = config.get('mail.imapPort', 993)
        self.config = config

        self.client = imaplib.IMAP4_SSL(host, port)


    def _get_email_content_by_uid(self, uid):
        """
        根据邮件唯一标识符(UID)获取邮件内容。

        :param uid: 邮件的唯一标识符
        :param imapclient: IMAP客户端实例
        :return: 邮件内容的字节流，如果获取失败则返回 None
        """
        # 根据 UID 获取邮件数据
        email_id = f"{uid}"
        status, msg_data = self.client.fetch(email_id, '(RFC822)')
        
        if status != 'OK':
            raise Exception(f"获取 UID 为 {uid} 的邮件内容时出错: {status}")
        if msg_data[0] is None:
            raise Exception(f"获取 UID 为 {uid} 的邮件内容时出错: 邮件数据为空")

        # 解析邮件
        msg = email.message_from_bytes(msg_data[0][1])  # pyright: ignore[reportArgumentType]
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
     

    def test_email_fetch(self):
        username = self.config.get('mail.emailAddress', '')
        password = self.config.get('mail.emailPassword', '')
        self.client.login(username, password)
        # 选择文件夹
        self.client.select("INBOX")
        c = self._get_email_content_by_uid(3329)
        print(c)

        self.client.logout()

