import json
import os

class Config:
    def __init__(self):
        self.tcp_host = "0.0.0.0"
        self.tcp_port = 5000
        self.websocket_host = "0.0.0.0"
        self.websocket_port = 8080
        # 日志等级为主机
        self.log_level = "INFO"
        
        # 尝试从配置文件加载 取决于工程本地有没有json文件
        # json文件格式：
        """
        {
            "tcp_host": "0.0.0.0",
            "tcp_port": 5000,
            "websocket_host": "0.0.0.0",
            "websocket_port": 8080,
            "log_level": "INFO"
        }
        """
        self._load_config()
    
    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                for key, value in config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

config = Config()