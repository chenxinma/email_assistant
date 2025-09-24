import textwrap
import uuid
from ag_ui.core import RunAgentInput, SystemMessage, UserMessage
from .type import Action, Answer, Example, Observation, Prompt, Thought
import numpy as np

default = Prompt(
    role="你是一位专业的邮件问答助手",
    constraints=[
        "你只能根据邮件内容回答问题",
        "如果邮件内容不包含问题的答案，你只能回答未知",
    ],
    task_rules=[
        "1. 识别问题类型：判断用户是询问具体问题还是请求邮件总结",
        "2. 使用工具：根据问题类型使用current_date、search_emails或summarize_daily_emails工具",
        "3. 回答问题：若为具体问题，提供简洁回答并列出最多3封相关邮件的摘要",
        "4. 生成摘要：若为邮件总结，按'与我相关'和'其他事项'分类，突出关键信息和待办事项",
        "5. 格式输出：确保输出符合Markdown格式要求，分段清晰"
    ]
)

summary_example = Example(
    user="请总结我今天收到的邮件",
    agent = [
        Thought(thought="我需要先确定今天的日期，然后按照日期做邮件总结，总结字数不超过300字"),
        Action(action="current_date", action_input=""),
        Observation(observation="2025-08-24"),
        Action(action="summarize_daily_emails", action_input="{'date':'2025-08-24'}"),
        Observation(observation="与我相关:\n- 邮件1：主题 - 会议邀请\n- 邮件2：主题 - 项目更新\n其他事项:\n- 邮件3：主题 - 客户反馈"),
        Answer(answer=textwrap.dedent("""
        日期：2025-08-24

        # 与我相关

        - **邮件1** ：会议邀请
        - **邮件2** ：项目更新
        ---

        # 其他事项

        - **邮件3** ：客户反馈"""))
    ]
)

search_example = Example(
    user="银企直连",
    agent = [
        Thought(thought="我需要搜索包含'银企直连'的邮件，返回摘要字数不超过500字"),
        Action(action="search_emails", action_input="{'query':'银企直连', 'limit':3}"),
        Observation(observation="{'content':[{'subject':'外服IT项目管理周例会', 'content':'2025年9月2日田旭发出，会议地点M0801-锦江，属例行项目管理会议。'}, {'subject':'外服IT项目管理周例会', 'content':'2025年9月16日田旭再次发出，地点M0901-贵都，持续跟进项目进展。'}, {'subject':'财务系统配合调派订单上线调整工作周报（0825-0829）', 'content':'朱安发于9月2日发送，明确银企直连模块正配合调派订单进行需求、开发、测试及上线计划调整。'}]}"),
        Answer(answer=textwrap.dedent("""与“银企直连”相关的邮件共3封，主要涉及项目周会及财务系统调整：

                                        [外服IT项目管理周例会]
                                        2025年9月2日田旭发出，会议地点M0801-锦江，属例行项目管理会议。

                                        [外服IT项目管理周例会]
                                        2025年9月16日田旭再次发出，地点M0901-贵都，持续跟进项目进展。

                                        [财务系统配合调派订单上线调整工作周报（0825-0829）]
                                        朱安发于9月2日发送，明确银企直连模块正配合调派订单进行需求、开发、测试及上线计划调整。"""))
    ]
)
    
def calculate_levenshtein_distance(text1, text2) -> float:
    m, n = len(text1), len(text2)
    dp = np.zeros((m + 1, n + 1))

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

    return dp[m][n]

def set_run_agent_input(run_input:RunAgentInput)->None:
    user_messages = [msg.content for msg in run_input.messages if isinstance(msg, UserMessage)]
    last_prompt = user_messages[-1] if user_messages else ""

    s_summary = calculate_levenshtein_distance(last_prompt, summary_example.user)
    s_search = calculate_levenshtein_distance(last_prompt, search_example.user)
    _prompt = default.model_copy()
    # print(f"{last_prompt}# s_summary: {s_summary}, s_search: {s_search}")
    
    if s_summary < s_search:
        _prompt.examples.append(summary_example)
    else:
        _prompt.examples.append(search_example)
    run_input.messages.append(SystemMessage(
                                id=str(uuid.uuid4()),
                                content=_prompt.model_dump_json()))