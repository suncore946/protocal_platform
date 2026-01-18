import json
from datetime import datetime
from urllib.parse import urljoin
from typing import Dict, Any, Type, Optional
from app.database import db
from app.config import GAME_SERVER
from .base import BaseProtocolHandler
from .http import HttpProtocolHandler
from .socket import SocketProtocolHandler
from .protobuf import ProtobufProtocolHandler
from .enums import CallType

# 协议处理器注册表
HANDLER_REGISTRY: Dict[CallType, Type[BaseProtocolHandler]] = {
    CallType.HTTP: HttpProtocolHandler,
    CallType.SOCKET: SocketProtocolHandler,
    CallType.PROTOBUF: ProtobufProtocolHandler,
}

def get_handler(call_type: CallType) -> BaseProtocolHandler:
    """工厂方法：根据类型获取处理器实例"""
    handler_class = HANDLER_REGISTRY.get(call_type)
    if not handler_class:
        raise ValueError(f"Unknown call_type: {call_type}")
    return handler_class()

def execute_protocol(protocol_row: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一入口函数，用于向下兼容旧的调用方式
    """
    raw_call_type = (protocol_row["call_type"] or "socket").lower()
    try:
        call_type = CallType(raw_call_type)
    except ValueError:
        return {"error": f"Unknown or unsupported call_type: {raw_call_type}"}
    
    # 解析目标配置
    target_config = json.loads(protocol_row["target_config_json"] or "{}")
    
    config = target_config.copy()

    # 处理全局 URL (仅针对 HTTP)
    if call_type == CallType.HTTP:
        global_url = db.get_setting("global_target_url", GAME_SERVER)
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

def log_protocol_test(
    username: str,
    protocol_name: str,
    target_url: str,
    request_params: Any,
    response_data: Any,
    assertions: Any = None
):
    """
    记录协议测试历史到数据库。
    """
    try:
        conn = db.connection
        conn.execute(
            """
            INSERT INTO history (
                username, action, protocol_name, target_url, 
                request_body, response_body, assertions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username, 
                "test_protocol", 
                protocol_name, 
                target_url,
                json.dumps(request_params, ensure_ascii=False) if not isinstance(request_params, str) else request_params,
                json.dumps(response_data, ensure_ascii=False) if not isinstance(response_data, str) else response_data,
                json.dumps(assertions, ensure_ascii=False) if assertions and not isinstance(assertions, str) else (assertions or "[]"),
                datetime.utcnow().isoformat() + "Z"
            ),
        )
        conn.commit()
    except Exception as e:
        # 避免日志记录失败影响主流程，仅打印错误
        print(f"Failed to log history: {e}")

