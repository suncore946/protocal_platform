import requests
from typing import Any, Dict
from .base import BaseProtocolHandler

class HttpProtocolHandler(BaseProtocolHandler):
    """HTTP 协议处理器"""
    
    def execute(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get("url")
        method = config.get("method", "GET").upper()
        if not url:
            raise ValueError("Missing URL configuration")

        if method == "GET":
            resp = requests.get(url, params=params, timeout=5)
        else:
            resp = requests.post(url, json=params, timeout=5)
        
        try:
            return resp.json()
        except ValueError:
            return {"raw_text": resp.text, "status_code": resp.status_code}
