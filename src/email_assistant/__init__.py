"""
邮件助手应用包
"""

import sys
from .main import run, DB_FILE
from .email_processor import EmailPresistence
from .api import run as api_run

def main():
    """应用入口"""
    if '--init' in sys.argv:
        EmailPresistence.init_database(DB_FILE)
    elif '--api' in sys.argv:
        api_run()
    else:
        run()
