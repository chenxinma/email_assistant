import unittest
from email.header import decode_header
from src.email_assistant.email_processor import EmailClient


class TestEmailProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = EmailClient("imap.qq.com", 993, "123456", "123456")

    def test_header_decode_with_utf8(self):
        # 测试UTF-8编码的邮件头
        encoded_header = '=?UTF-8?Q?=E6=B5=8B=E8=AF=95?='
        decoded = self.processor.header_decode(encoded_header)
        self.assertEqual(decoded, '测试')

    def test_header_decode_with_gbk(self):
        # 测试GBK编码的邮件头
        encoded_header = '=?GBK?Q?=B2=E2=CA=D4?='
        decoded = self.processor.header_decode(encoded_header)
        self.assertEqual(decoded, '测试')

    def test_header_decode_with_latin1(self):
        # 测试Latin-1编码的邮件头
        encoded_header = 'chenxin.ma@fsg'
        decoded = self.processor.header_decode(encoded_header)
        self.assertEqual(decoded, 'chenxin.ma@fsg')

    def test_header_decode_with_other(self):
        encoded_header = '=?UTF-8?Q?=E6=9D=8E=E5=9B=9B?= <li.si@example.com>'
        decoded = self.processor.header_decode(encoded_header)
        self.assertEqual(decoded, '李四 <li.si@example.com>')
