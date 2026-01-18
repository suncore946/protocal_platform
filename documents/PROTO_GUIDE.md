# Protocol Buffers (Protobuf) 协议指南

## 1. 什么是 Protobuf？

**Protocol Buffers** (简称 Protobuf) 是 Google 开发的一种语言无关、平台无关、可扩展的序列化结构数据格式。

简单来说，它和 JSON 或 XML 很像，都是用来在网络间传输数据的。但它有显著的不同：
- **二进制格式**：它传输的是二进制流，而不是文本。因此体积更小，传输和解析速度更快。
- **强类型契约**：必须预先定义数据结构（Schema）。发送方和接收方必须严格遵守这个结构。

## 2. 它在协议测试中起什么作用？

在测试系统中，Protobuf 的核心作用是 **“翻译”**：
1. **编码 (Serialization)**：将你在网页表单里填写的 `user_id="1001"` 这样的易读数据，按照严格的格式压缩成二进制数据包（例如 `\x08\xe9\x07`）。
2. **解码 (Deserialization)**：接收服务端返回的看不懂的二进制流，翻译回 `{ "result_code": 0, "message": "Success" }` 这样的可读 JSON 格式供你查看。

如果没有这个定义层，客户端和服务端就犹如“鸡同鸭讲”，无法理解对方发送的字节流含义。

---

## 3. 全链路实现细节 (在本框架中)

本框架经过优化，支持 **纯 Python (Pure Python)** 模式。这意味着你 **不需要** 安装复杂的 `protoc` 编译器，也不需要编写 `.proto` 文件。直接用 Python 代码定义结构即可。

### 步骤 1：定义协议结构

在 `app/protos/` 目录下创建一个新的 Python 文件。例如： `app/protos/order_protocol.py`。
我们需要定义“发给服务端的数据结构 (Request)”和“服务端回给我们的数据结构 (Response)”。

**代码规范：**
使用 `@dataclass` 装饰器和 `pure_protobuf` 库。

```python
from dataclasses import dataclass
from pure_protobuf.types import int32, int64
from pure_protobuf.annotations import Field

# 定义请求结构
@dataclass
class CreateOrderRequest:
    # Field(序号, default=默认值)
    # 序号必须与服务端定义一致！
    user_id: int64 = Field(1, default=0)
    product_id: int32 = Field(2, default=0)
    amount: int32 = Field(3, default=1)
    note: str = Field(4, default="")

# 定义响应结构
@dataclass
class CreateOrderResponse:
    order_id: str = Field(1, default="")
    status: int32 = Field(2, default=0)
    message: str = Field(3, default="")
```

### 步骤 2：在 test_cases 目录下创建 YAML 配置

不再修改 `config.yaml`。请在 `test_cases/` 目录下创建一个新的 YAML 文件，例如 `test_cases/order_test.yaml`。

**关键配置项说明：**
- `call_type`: 必须填 `protobuf`。
- `proto_module`: 指向你刚才创建的文件路径 (以 `app.` 开头，例如 `app.protos.order_protocol`)。
- `request_class`: 你定义的请求类 (Request Class)。
- `response_class`: 你定义的响应类 (Response Class)。
- `test_cases`: 这里可以定义多组预设参数，方便快速切换测试场景。

```yaml
name: "创建订单测试"
call_type: "protobuf"
target_config:
  host: "127.0.0.1"      # 服务端 IP
  port: 9000             # 服务端端口
  proto_module: "app.protos.order_protocol" # 指向步骤1的文件
  request_class: "CreateOrderRequest"
  response_class: "CreateOrderResponse"
description: "测试订单创建流程"

# 定义网页上的默认输入表单
params:
  user_id:
    type: "integer"
    default: 10086
  product_id:
    type: "integer"
    default: 500
  amount:
    type: "integer"
    default: 2
  note:
    type: "string"
    default: "加急配送"

# 定义多组测试用例
test_cases:
  - name: "常规订单"
    params:
      user_id: 10086
      product_id: 500
      amount: 1
      note: "普通"
  - name: "大额订单"
    params:
      user_id: 88888
      product_id: 999
      amount: 100
      note: "VIP客户"
```

### 步骤 3：重启并测试

无需编译代码，只需重启服务即可加载并在网页上看到新的测试项。

```bash
python run.py
```

### 底层执行流程 (框架内部工作原理)

当你点击网页上的“运行”按钮时，框架内部（`app/connect/protobuf.py`）会执行以下操作：

1. **动态加载**：根据配置文件中的 `app.protos.order_protocol`，Python 动态导入该模块。
2. **数据填充**：读取网页提交的 JSON 参数 (`user_id=10086`), 实例化 `CreateOrderRequest(user_id=10086, ...)` 对象。
3. **序列化**：调用 `req_obj.dumps()` 将对象转为二进制字节流 (bytes)。
4. **封包发送**：
   - 框架采用常见的 **Length-Prefixed** 封包格式。
   - 先发送 4 字节的大端序整数 (表示包体长度)。
   - 再发送真正的 Protobuf 二进制包体。
5. **接收响应**：
   - 先读取 4 字节长度头。
   - 再读取指定长度的二进制数据。
6. **反序列化**：调用 `CreateOrderResponse.loads(bytes)` 将二进制还原为对象。
7. **结果展示**：将对象转为字典 (Dict)，最终在网页上以 JSON 形式展示给用户。

## 4. 总结

要在本框架增加一个新的 Protobuf 协议：

1. **写 Python 类** (`app/protos/xxx.py`)：描述数据长什么样。
2. **写配置 YAML** (`test_cases/xxx.yaml`)：定义协议参数和测试用例（如 "常规订单"、"异常测试" 等）。
3. **重启 run.py**：框架自动加载所有配置。
