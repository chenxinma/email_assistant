from datetime import datetime
import logging
import os
from pathlib import Path

# Configure logging
def setup_logging(name:str):
    LOCAL_DIR = Path(__file__).parent.parent
    log_dir = os.path.join(LOCAL_DIR / "../", 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f'ad-agent_{datetime.now().strftime("%Y%m%d")}.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )
    return logging.getLogger(name)