"""
配置管理模块
"""

import json
import os
from typing import Dict, Any, Optional

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
                    "indexedFolders": ["INBOX"]
                },
                "ai": {
                    "model": "all-MiniLM-L6-v2",
                    "summaryLength": 300
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
    
    def get(self, key_path: str, default=None):
        """获取配置项"""
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
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