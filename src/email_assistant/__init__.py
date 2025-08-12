"""
邮件助手应用包
"""

import sys
from .main import run, init_database , fetch_emails
import asyncio

def main():
    """应用入口"""
    if '--init' in sys.argv:
        init_database()
    elif '--fetch' in sys.argv:
        asyncio.run(fetch_emails())
    else:
        run()
