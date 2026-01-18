from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseProtocolHandler(ABC):
    """协议处理器基类"""
    
    @abstractmethod
    def execute(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行协议调用
        :param config: 协议配置 (如 url, host, port 等)
        :param params: 调用参数
        :return: 调用结果字典
        """
        pass
