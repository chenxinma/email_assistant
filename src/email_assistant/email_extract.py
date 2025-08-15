import os
import re
import sqlite3
import textwrap
from typing import Generator, List

from dotenv import load_dotenv
from icalendar import Calendar
import jieba
import langextract as lx
from langextract.data import AnnotatedDocument
from langextract.inference import BaseLanguageModel
from openai import OpenAI

from .type import Email, EmailAttribute

examples = [
    lx.data.ExampleData(
        text=textwrap.dedent("""Dear 马老师，
           本次大数据平台安装JVM工具主要是用于监控各组件JVM信息，包括记录pod重启情况、监控jvm老年代使用过高时自动保存jmpa与jstack等功能。目前在测试环境已通过测试，更多细节说明可见附件文档，感谢。
        """),
        extractions=[
            lx.data.Extraction(
                extraction_class="收件对象",
                extraction_text="马老师",
            ),
            lx.data.Extraction(
                extraction_class="关注的日期时间",
                extraction_text="-",
            ),
            lx.data.Extraction(
                extraction_class="主要内容",
                extraction_text="安装JVM工具",
            ),
        ]
    ),
    lx.data.ExampleData(
        text=textwrap.dedent("""各位同事：
            请提供附件中截止2025年9月底，合同即将到期的IT采购计划进度，谢谢。
            另外，如有以下情况的，也请同步更新支付计划清单，并标黄，谢谢。
            1，“待支付”工作表中已完成付款的，请转移到“已支付”工作表中；
            2，新增已确认，未支付的合同/订单，请添加至“待支付”工作表中；
            3，支付计划仅统计计入信管部部门预算的合同/订单；
            4，合同/订单分多笔支付的，请拆分成多行添加。
        """),
        extractions=[
            lx.data.Extraction(
                extraction_class="收件对象",
                extraction_text="各位同事",
            ),
            lx.data.Extraction(
                extraction_class="关注的日期时间",
                extraction_text="2025年9月底",
            ),
            lx.data.Extraction(
                extraction_class="主要内容",
                extraction_text="提供合同到期进度",
            ),
        ]
    ),
    lx.data.ExampleData(
        text=textwrap.dedent("""HI 马老师：
                                附件为上海外服（集团）有限公司飞致云堡垒机的报价，敬请查收，谢谢！
        """),
        extractions=[
            lx.data.Extraction(
                extraction_class="收件对象",
                extraction_text="马老师",
            ),
            lx.data.Extraction(
                extraction_class="关注的日期时间",
                extraction_text="-",
            ),
            lx.data.Extraction(
                extraction_class="主要内容",
                extraction_text="飞致云堡垒机报价",
            ),
        ]
    ),
]

class QwenDashScopeModel(BaseLanguageModel):
    def __init__(self, model_id: str, **kwargs):
        super().__init__()
        load_dotenv()
        self.model_id = model_id
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", ""),
        )
    
    def infer(self, batch_prompts, **kwargs):
        # Implement inference
        for prompt in batch_prompts:
            result = self._call_api(prompt)
            yield [lx.inference.ScoredOutput(score=1.0, output=result)]
    
    def _call_api(self, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}, ]
        )
        return response.choices[0].message.content  # pyright: ignore[reportReturnType]


def extract_email_info(emails: List[Email], model_id:str) -> Generator[EmailAttribute, None, None]:
    """抽取读取邮件，邮件收件对象、关注的日期时间、主要内容"""
    # 过滤出包含icalendar的邮件
    cal_emails = []
    # 过滤出一般邮件
    any_emails = []
    for email in emails:
        if email.content.startswith("BEGIN:VCALENDAR"):
            cal_emails.append(email)
        else:
            any_emails.append(email)

    # 抽取icalendar邮件
    for email in cal_emails:
        cal = Calendar.from_ical(email.content)
        for component in cal.walk():
            if component.name == "VEVENT":
                row = EmailAttribute(
                    uid= int(email.uid),
                    recipient=email.recipient,
                    datetime=component.get('dtstart').dt.strftime("%Y-%m-%d %H:%M:%S"),
                    content=textwrap.dedent(f"""会议邀请
                    会议主题：{component.get('summary')}
                    会议地点：{component.get('location')}
                    """)
                )
                yield row

    docs = [
        lx.data.Document(
            text=f"""
                subject:{email.subject}
                sender:{email.sender}
                content:{email.content}
            """.strip()[:1000],
            document_id=str(email.uid),
        )
        for email in any_emails
    ]
    lx_prompt = "抽取邮件收件对象、日期时间、主要内容。主要内容要简短，概括到300字以内。"
 
    result = lx.extract(
        text_or_documents=docs,
        prompt_description=lx_prompt,
        examples=examples,
        language_model_type=QwenDashScopeModel,
        model_id=model_id
    )
    if isinstance(result, AnnotatedDocument):
        result = [result]

    for doc in result:
        if doc.extractions:
            row = EmailAttribute(
                uid= int(doc.document_id),
            )
            for e in doc.extractions:
                if e.extraction_class == "收件对象":
                    row.recipient = e.extraction_text
                elif e.extraction_class == "关注的日期时间":
                    row.datetime = e.extraction_text
                elif e.extraction_class == "主要内容":
                    row.content = e.extraction_text
            yield row

def extract_tasks(text: str) -> List[str]:
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