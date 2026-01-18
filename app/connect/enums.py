from enum import Enum

class CallType(str, Enum):
    HTTP = "http"
    SOCKET = "socket"
    PROTOBUF = "protobuf"
