"""
邮件助手应用包
"""

import sys
from .main import run, DB_FILE
from .email_processor import EmailPresistence

def main():
    """应用入口"""
    if '--init' in sys.argv:
        EmailPresistence.init_database(DB_FILE)
    else:
        run()
