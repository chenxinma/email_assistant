"""
配置管理模块
"""

import json
import os
from typing import Dict, Any, Optional, Union, TypeVar

ConfigValueT = TypeVar('ConfigValueT', str, int, Dict[str, Any], None)

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认配置
            config = {
                "mail": {
                    "refreshInterval": 15,
                    "indexedFolders": ["INBOX"],
                    "emailAddress": "chenxin.ma@fsg.com.cn",
                    "emailPassword": "your_email_password",
                    "imapServer": "imaphz.qiye.163.com",
                    "imapPort": 993,
                    "smtpServer": "smtphz.qiye.163.com",
                    "smtpPort": 465
                },
                "ai": {
                    "embeddingModel": "bge-large-zh-v1.5",
                    "embeddingBaseUrl": "http://172.16.37.21:9997/v1",
                    "summaryLength": 512
                }
            }
            self.save_config(config)
            return config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """保存配置文件"""
        if config is not None:
            self.config = config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get(self, key_path: str, default:ConfigValueT=None)-> ConfigValueT:
        """获取配置项"""
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value  # type: ignore
        except KeyError:
            return default
    
    def set(self, key_path: str, value: Any):
        """设置配置项"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()