import json
from urllib.parse import urljoin
from typing import Dict, Any, Type
from app.database import get_setting
from .base import BaseProtocolHandler
from .http import HttpProtocolHandler
from .socket import SocketProtocolHandler
from .protobuf import ProtobufProtocolHandler
from .local import LocalProtocolHandler

# 协议处理器注册表
HANDLER_REGISTRY: Dict[str, Type[BaseProtocolHandler]] = {
    "http": HttpProtocolHandler,
    "socket": SocketProtocolHandler,
    "protobuf": ProtobufProtocolHandler,
    "local": LocalProtocolHandler,
}

def get_handler(call_type: str) -> BaseProtocolHandler:
    """工厂方法：根据类型获取处理器实例"""
    handler_class = HANDLER_REGISTRY.get(call_type.lower())
    if not handler_class:
        raise ValueError(f"Unknown call_type: {call_type}")
    return handler_class()

def execute_protocol(protocol_row: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一入口函数，用于向下兼容旧的调用方式
    """
    call_type = (protocol_row["call_type"] or "socket").lower()
    
    # 解析目标配置
    target_config = json.loads(protocol_row["target_config_json"] or "{}")
    
    # 将协议名称合并到配置中 (供 LocalHandler 使用)
    config = target_config.copy()
    config["name"] = protocol_row["name"]

    # 处理全局 URL (仅针对 HTTP)
    if call_type == "http":
        global_url = get_setting("global_target_url", "http://game_backend.com")
        relative_url = config.get("url", "")
        # 如果是相对路径或为空，则拼接全局 URL
        if not relative_url.lower().startswith(("http://", "https://")):
            # urljoin 处理 path 拼接很智能
            # 比如 base="http://a.com/api", path="/login" -> "http://a.com/login"
            # 比如 base="http://a.com/api/", path="login" -> "http://a.com/api/login"
            config["url"] = urljoin(global_url, relative_url)
    
    try:
        handler = get_handler(call_type)
        return handler.execute(config, params)
    except Exception as e:
        return {"error": str(e)}
