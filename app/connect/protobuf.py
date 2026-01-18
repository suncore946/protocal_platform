import socket
import struct
import importlib
from typing import Any, Dict
from google.protobuf import json_format
from .base import BaseProtocolHandler

class ProtobufProtocolHandler(BaseProtocolHandler):
    """Protobuf over TCP 协议处理器"""
    
    def execute(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        host = config.get("host")
        port = config.get("port")
        module_name = config.get("proto_module")
        req_class_name = config.get("request_class")
        res_class_name = config.get("response_class")

        if not all([host, port, module_name, req_class_name, res_class_name]):
            raise ValueError("Missing protobuf configuration")

        # 动态加载模块和类
        module = importlib.import_module(module_name)
        ReqClass = getattr(module, req_class_name)
        ResClass = getattr(module, res_class_name)

        # 构造请求对象
        req_obj = ReqClass()
        json_format.ParseDict(params, req_obj, ignore_unknown_fields=True)
        req_bytes = req_obj.SerializeToString()

        # 发送 (Length-Prefixed: 4 bytes big-endian length + body)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, int(port)))
            
            # 发送长度 + 内容
            length_prefix = struct.pack(">I", len(req_bytes))
            s.sendall(length_prefix + req_bytes)
            
            # 接收响应长度
            length_data = s.recv(4)
            if not length_data or len(length_data) < 4:
                raise IOError("Failed to read response length")
            
            (resp_len,) = struct.unpack(">I", length_data)
            
            # 接收响应内容
            resp_bytes = b""
            while len(resp_bytes) < resp_len:
                chunk = s.recv(min(4096, resp_len - len(resp_bytes)))
                if not chunk:
                    break
                resp_bytes += chunk
            
            if len(resp_bytes) != resp_len:
                raise IOError(f"Incomplete response. Expected {resp_len}, got {len(resp_bytes)}")

            # 解析响应
            res_obj = ResClass()
            res_obj.ParseFromString(resp_bytes)
            
            return json_format.MessageToDict(res_obj, preserving_proto_field_name=True)
