"""
app.protos 包
-------------

该目录用于存放 Protocol Buffers (.proto) 定义文件及其编译生成的 Python 代码。

文件说明：
- demo.proto: 
    原始的协议定义文件，使用 Protobuf 语法编写。
    定义了数据结构（Message）和服务接口（Service，如果涉及到 gRPC）。

- demo_pb2.py: 
    由 `protoc` 编译器根据 demo.proto 自动生成的 Python 代码。
    包含了 demo.proto 中定义的消息类型的 Python 类（如 UserRequest, UserResponse）。
    **注意**：请勿直接手动修改此文件，修改 demo.proto 后应重新编译。

重新生成代码示例命令 (在项目根目录下):
    protoc -I=. --python_out=. app/protos/demo.proto
"""
