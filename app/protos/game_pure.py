from dataclasses import dataclass
from pure_protobuf.types import int32
from pure_protobuf.annotations import Field

# 纯 Python 定义的 Protocol Buffers 消息
# 使用 pure-protobuf 库，无需 protoc 编译

@dataclass
class LoginRequest:
    username: str = Field(1, default="")
    password: str = Field(2, default="")
    server_id: int32 = Field(3, default=0)
    device_id: str = Field(4, default="")

@dataclass
class UserProfile:
    user_id: int32 = Field(1, default=0)
    nickname: str = Field(2, default="")
    level: int32 = Field(3, default=0)
    register_time: int32 = Field(4, default=0) # timestamp

@dataclass
class LoginResponse:
    result_code: int32 = Field(1, default=0)
    error_message: str = Field(2, default="")
    token: str = Field(3, default="")
    profile: UserProfile = Field(4, default_factory=UserProfile)
