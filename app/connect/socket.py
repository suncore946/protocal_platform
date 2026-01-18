import json
import socket
from typing import Any, Dict
from .base import BaseProtocolHandler

class SocketProtocolHandler(BaseProtocolHandler):
    """Socket (JSON over TCP) 协议处理器"""
    
    def execute(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        host = config.get("host")
        port = config.get("port")
        if not host or not port:
            raise ValueError("Missing host/port configuration")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, int(port)))
            # 发送数据：JSON 字符串
            msg = json.dumps(params)
            s.sendall(msg.encode('utf-8'))
            
            # 接收数据
            data = s.recv(4096)
            if not data:
                return {}
            return json.loads(data.decode('utf-8'))
