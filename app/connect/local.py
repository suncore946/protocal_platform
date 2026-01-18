import random
from datetime import datetime
from typing import Any, Dict
from .base import BaseProtocolHandler

class LocalLogic:
    """存放具体的本地业务逻辑 (Legacy)"""
    @staticmethod
    def user_query(params):
        user_id = params.get("user_id", "0")
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "user_id": user_id,
                "name": f"User_{user_id}",
                "level": random.randint(1, 100),
                "last_active": datetime.now().isoformat()
            }
        }

    @staticmethod
    def order_create(params):
        amount = params.get("amount", 0)
        currency = params.get("currency", "CNY")
        order_id = f"ODR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}"
        return {
            "code": 0,
            "message": "success",
            "data": {
                "order_id": order_id,
                "amount": amount,
                "currency": currency,
                "status": "created"
            }
        }

class LocalProtocolHandler(BaseProtocolHandler):
    """本地函数调用协议处理器"""
    
    def execute(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        # 从配置中获取要调用的方法名，之前是 hardcode name，现在建议显式配置 method 或 function
        method_name = config.get("method") or config.get("function")
        
        if not method_name:
            raise ValueError(f"Missing local method/function name in config for {config.get('name')}")

        if not hasattr(LocalLogic, method_name):
             raise ValueError(f"Local method '{method_name}' not found in LocalLogic")

        handler_func = getattr(LocalLogic, method_name)
        return handler_func(params)
