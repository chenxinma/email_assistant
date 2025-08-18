import datetime
import unittest

import sqlite3

import sqlite_vec
from email_assistant.main import DB_FILE
from email_assistant.ai_processor import AIProcessor, summary_cache
from email_assistant.type import DailyMailSummary
from email_assistant.log_config import setup_logging

logger = setup_logging(__name__)

class TestAIProcessorGenerateSummary(unittest.IsolatedAsyncioTestCase):
    """测试 AIProcessor.generate_summary 方法"""

    async def asyncSetUp(self):
        """初始化测试环境"""
        # 创建内存数据库连接
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

        # 重置缓存
        summary_cache.clear()

        # 创建 AIProcessor 实例，模拟 summary_agent
        self.processor = AIProcessor(embedding_base_url="https://example.com")

    async def asyncTearDown(self):
        """清理测试环境"""
        self.conn.close()
        summary_cache.clear()

    async def test_generate_summary_with_multiple_emails(self):
        """测试多封邮件的情况"""
        # 插入更多测试数据
        test_date = datetime.date(2025, 8, 18)

        # 执行测试
        result = await self.processor.generate_summary(test_date, "测试用户", self.conn)

        # 验证结果
        self.assertIsInstance(result, DailyMailSummary)
        logger.info("="*20)
        logger.info(result)

if __name__ == '__main__':
    unittest.main()