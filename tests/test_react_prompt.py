import unittest
import uuid
from ag_ui.core import AssistantMessage, RunAgentInput, UserMessage
from email_assistant.react.prompt import set_run_agent_input

class TestSetRunAgentInput(unittest.TestCase):
    """测试 set_run_agent_input 函数"""

    def setUp(self):
        """初始化测试环境"""
        pass

    def tearDown(self):
        """清理测试环境"""
        pass

    def test_set_run_agent_input_with_summary_query(self):
        """测试使用总结查询时的函数行为"""
        # 创建测试用的RunAgentInput对象
        run_input = RunAgentInput(
            thread_id=str(uuid.uuid4()),
            run_id=str(uuid.uuid4()),
            state={},
            context=[],
            messages=[
                UserMessage(id=str(uuid.uuid4()), content="请总结我今天收到的邮件")
            ],
            tools=[],  # 空tools列表
            forwarded_props=None
        )

        # 调用待测试函数
        set_run_agent_input(run_input)

        # 验证结果：检查是否添加了AssistantMessage
        self.assertEqual(len(run_input.messages), 2)
        self.assertIsInstance(run_input.messages[1], AssistantMessage)
        
        # 验证AssistantMessage中的内容是有效的JSON格式
        assistant_message = run_input.messages[1]
        self.assertTrue(isinstance(assistant_message.content, str))
        self.assertTrue(len(assistant_message.content) > 0)  # pyright: ignore[reportArgumentType]
        self.assertTrue("role" in assistant_message.content)  # pyright: ignore[reportOperatorIssue]
        self.assertTrue("examples" in assistant_message.content)  # pyright: ignore[reportOperatorIssue]
    

    def test_set_run_agent_input_with_summary_query_date(self):
        """测试使用总结查询时的函数行为"""
        # 创建测试用的RunAgentInput对象
        run_input = RunAgentInput(
            thread_id=str(uuid.uuid4()),
            run_id=str(uuid.uuid4()),
            state={},
            context=[],
            messages=[
                UserMessage(id=str(uuid.uuid4()), content="请总结我2023-08-22收到的邮件")
            ],
            tools=[],  # 空tools列表
            forwarded_props=None
        )

        # 调用待测试函数
        set_run_agent_input(run_input)

        # 验证结果：检查是否添加了AssistantMessage
        self.assertEqual(len(run_input.messages), 2)
        self.assertIsInstance(run_input.messages[1], AssistantMessage)
        
        # 验证AssistantMessage中的内容是有效的JSON格式
        assistant_message = run_input.messages[1]
        self.assertTrue(isinstance(assistant_message.content, str))
        self.assertTrue(len(assistant_message.content) > 0)  # pyright: ignore[reportArgumentType]
        self.assertTrue("role" in assistant_message.content)  # pyright: ignore[reportOperatorIssue]
        self.assertTrue("examples" in assistant_message.content)  # pyright: ignore[reportOperatorIssue]

    def test_set_run_agent_input_with_search_query(self):
        """测试使用搜索查询时的函数行为"""
        # 创建测试用的RunAgentInput对象
        run_input = RunAgentInput(
            thread_id=str(uuid.uuid4()),
            run_id=str(uuid.uuid4()),
            state={},
            context=[],
            messages=[
                UserMessage(id=str(uuid.uuid4()), content="短信")
            ],
            tools=[],  # 空tools列表
            forwarded_props=None
        )

        # 调用待测试函数
        set_run_agent_input(run_input)

        # 验证结果：检查是否添加了AssistantMessage
        self.assertEqual(len(run_input.messages), 2)
        self.assertIsInstance(run_input.messages[1], AssistantMessage)
        
        # 验证AssistantMessage中的内容是有效的JSON格式
        assistant_message = run_input.messages[1]
        self.assertTrue(isinstance(assistant_message.content, str))
        self.assertTrue(len(assistant_message.content) > 0)  # pyright: ignore[reportArgumentType]
        self.assertTrue("role" in assistant_message.content)  # pyright: ignore[reportOperatorIssue]
        self.assertTrue("examples" in assistant_message.content)  # pyright: ignore[reportOperatorIssue]

if __name__ == '__main__':
    unittest.main()