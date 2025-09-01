import sys
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 打印环境变量
print("Python executable path:", sys.executable)
print("OPENAI_BASE_URL:", os.getenv("OPENAI_BASE_URL"))
print("OPENAI_MODEL:", os.getenv("OPENAI_MODEL"))
print("CONFIG_FILE:", os.getenv("CONFIG_FILE"))
print("DB_FILE:", os.getenv("DB_FILE"))

# 获取当前工作目录
current_dir = os.getcwd()
print("当前工作目录：", current_dir)

if __name__ == '__main__':    
    from email_assistant import main
    main()