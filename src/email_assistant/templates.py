"""邮件模板管理模块
"""

from typing import List, Dict, Optional
from .main import Template, DB_FILE
import sqlite3

class TemplateManager:
    """模板管理类"""
    
    def __init__(self):
        self.templates = self.load_templates()
    
    def load_templates(self) -> List[Template]:
        """从数据库加载模板"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, subject, content
                FROM templates
            ''')
            
            templates = []
            for row in cursor.fetchall():
                templates.append(Template(
                    id=row[0],
                    name=row[1],
                    subject=row[2],
                    content=row[3]
                ))
            
            conn.close()
            
            # 如果没有模板，创建默认模板
            if not templates:
                self.create_default_templates()
                return self.load_templates()
            
            return templates
        except Exception as e:
            print(f"加载模板失败: {str(e)}")
            return []
    
    def create_default_templates(self):
        """创建默认模板"""
        default_templates = [
            Template(
                name="工作汇报",
                subject="【工作汇报】{date}工作情况",
                content="领导好：\n\n{date}工作情况如下：\n1. {task1}\n2. {task2}\n3. {task3}\n\n明日计划：\n1. {plan1}\n2. {plan2}\n\n谢谢！"
            ),
            Template(
                name="会议邀请",
                subject="【会议邀请】{topic}讨论会",
                content="各位同事：\n\n您好！\n\n我们计划于{time}召开{topic}讨论会，诚邀您参加。\n\n会议议题：\n1. {topic1}\n2. {topic2}\n\n会议地点：{location}\n\n请提前安排好工作，准时参加。\n\n谢谢！"
            )
        ]
        
        for template in default_templates:
            self.save_template(template)
    
    def get_template_by_name(self, name: str) -> Optional[Template]:
        """根据名称获取模板"""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_all_templates(self) -> List[Template]:
        """获取所有模板"""
        return self.templates
    
    def save_template(self, template: Template) -> bool:
        """保存模板"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            if template.id is None:
                # 新建模板
                cursor.execute('''
                    INSERT INTO templates (name, subject, content)
                    VALUES (?, ?, ?)
                ''', (template.name, template.subject, template.content))
                template.id = cursor.lastrowid
            else:
                # 更新模板
                cursor.execute('''
                    UPDATE templates
                    SET name = ?, subject = ?, content = ?
                    WHERE id = ?
                ''', (template.name, template.subject, template.content, template.id))
            
            conn.commit()
            conn.close()
            
            # 更新内存中的模板列表
            self.templates = self.load_templates()
            
            return True
        except Exception as e:
            print(f"保存模板失败: {str(e)}")
            return False
    
    def delete_template(self, template_id: int) -> bool:
        """删除模板"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM templates
                WHERE id = ?
            ''', (template_id,))
            
            conn.commit()
            conn.close()
            
            # 更新内存中的模板列表
            self.templates = self.load_templates()
            
            return True
        except Exception as e:
            print(f"删除模板失败: {str(e)}")
            return False
    
    def render_template(self, template_name: str, **kwargs) -> Dict[str, str]:
        """渲染模板"""
        template = self.get_template_by_name(template_name)
        if not template:
            raise ValueError(f"模板 '{template_name}' 不存在")
        
        # 替换占位符
        subject = template.subject
        content = template.content
        
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))
        
        return {
            "subject": subject,
            "content": content
        }
