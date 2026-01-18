# 协议测试平台（Flask + SQLite3）

## 1. 环境要求

- Python 3.10+（建议）
- Windows / Linux / macOS 均可

## 2. 创建虚拟环境

### Conda（推荐在已有 Anaconda/Miniconda 时使用）

#### 一条命令创建环境并安装依赖（推荐）

```bash
cd /path/to/project
conda env create -f environment.yml
conda activate protocol-demo
```

#### 手动创建环境（可选）

```bash
cd /path/to/project
conda create -n protocol-demo python=3.10
conda activate protocol-demo
```

### Windows (PowerShell)

```powershell
# 进入项目目录
cd ./protocal_platform
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
cd ./protocal_platform
python3 -m venv .venv
source .venv/bin/activate
```

## 3. 安装依赖

> 如果已使用 `environment.yml` 创建环境，可跳过此步骤。

```bash
pip install -r requirements.txt
```

## 4. 配置说明

- **主配置文件**：[config.yaml](config.yaml)，负责全局设置（如页面标题、数据库路径、日志等）。
- **协议配置文件**：`test_cases/` 目录下的所有 `.yaml` 文件。每个文件定义一个协议及其测试用例。

### 初始协议数据

协议数据不再存储在 `config.yaml` 中，而是分散管理在 `test_cases` 目录下。例如：

- `test_cases/game_login.yaml` - 游戏登录协议
- `test_cases/http_test.yaml` - HTTP 测试协议

## 5. 初始化与启动（开发模式）

```bash
python run.py
```

启动后访问：

- [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 6. 目录结构

```text
.
├── run.py                 # 启动入口 (原 app.py)
├── config.yaml            # 全局配置
├── test_cases/            # [新增] 协议定义与测试用例目录 (YAML)
│   ├── game_login.yaml
│   └── ...
├── app/
│   ├── protos/            # Protobuf 协议定义 (Python Dataclasses)
│   ├── blueprints/        # 路由蓝图
│   ├── connect/           # 协议连接适配器
│   ├── config.py          # 配置加载逻辑
│   ├── database.py        # 数据库模型
│   └── __init__.py        # App Factory
├── requirements.txt
├── app.db                 # 数据库 (自动生成)
├── logs/                  # 日志
├── templates/
└── static/
```

## 7. 常用接口

- `GET /api/protocols` 协议列表
- `GET /api/protocol/<id>` 协议详情
- `POST /api/protocol/<id>/call` 发起协议调用
- `POST /api/login` 登录（仅用户名）
- `POST /api/history` 记录用户操作

## 8. 生产部署（Windows 推荐：Waitress）

> Windows 上不建议使用 Gunicorn，可用 Waitress。

### 安装 Waitress

```bash
pip install waitress
```

### 启动

```bash
waitress-serve --listen=0.0.0.0:5000 run:app
```

## 9. 生产部署（Linux 示例：Gunicorn）

> 内网访问场景可直接使用 Gunicorn，无需反向代理。

### 安装 Gunicorn

```bash
pip install gunicorn
```

### 运行（示例）

```bash
gunicorn -w 2 -b 0.0.0.0:5000 run:app
```

## 10. 数据库说明

- 使用 SQLite3，首次启动自动建表
- 全局设置表：`settings`
- 操作历史表：`history`
- *注意：协议定义实时读取自 `test_cases/` 目录下的文件，不存储在数据库中*

## 11. 日志说明

- 使用 Loguru
- 日志文件位置：由 `config.yaml -> app.log_file` 指定

## 12. 快速构建协议测试请求

使用 `/api/protocol/<protocol_id>/call` 接口可以灵活地对协议进行测试。以下是构建请求的详细指南。

### 请求信息

- **URL**: `/api/protocol/<protocol_id>/call` (例如 `/api/protocol/1/call`)
- **Method**: `POST`
- **Content-Type**: `application/json`

### 请求体内字段说明

| 字段 | 类型 | 必填 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `params` | Object | 否 | 发送给协议的实际参数，支持嵌套。你可以在断言中通过 `params` 引用。 | `{"user_id": 1001}` |
| `concurrency` | Integer | 否 | 并发数，默认为 1。 | `5` |
| `with_random` | Boolean | 否 | 是否在响应中包含随机数（用于调试）。 | `true` |
| `assertions` | Array | 否 | **自定义断言列表**。支持 Python 表达式。可用变量：`response`(响应体), `params`(请求参数)。 | `["response['code'] == 0"]` |

### 完整请求示例

```json
{
  "concurrency": 1,
  "with_random": true,
  "params": {
    "user_id": 12345,
    "type": "vip"
  },
  "assertions": [
    "response['code'] == 200",
    "len(response['data']['items']) > 0",
    "response['data']['user_info']['id'] == params['user_id']"
  ]
}
```

### 响应示例包含断言结果

```json
{
  "protocol_id": 1,
  "protocol_name": "获取用户信息",
  "concurrency": 1,
  "results": [
    {
      "index": 1,
      "request_params": { "user_id": 12345, "type": "vip" },
      "response": { "code": 200, "data": { ... } },
      "assertions": [
        { "rule": "response['code'] == 200", "status": "pass" },
        { "rule": "len(response['data']['items']) > 0", "status": "fail" }
      ],
      "timestamp": "2023-10-27T10:00:00Z"
    }
  ]
}
```

---

## 13. 快速接入新协议

本平台支持通过添加 YAML 配置文件的方式快速接入新协议，无需修改代码。

### 接入步骤

1. **新建文件**：在 `test_cases/` 目录下创建一个新的 `.yaml` 文件（例如 `my_api.yaml`）。
2. **编写配置**：参照下方的格式编写协议定义。
3. **即时生效**：保存文件后，刷新页面或调用接口即可看到新协议，**不需要重启服务**。

### 配置字段详解

配置文件（YAML）支持以下根字段：

| 字段 | 必填 | 说明 |
| :--- | :--- | :--- |
| `name` | 是 | 协议的名称，显示在列表中。 |
| `description` | 否 | 协议描述/说明。 |
| `call_type` | 是 | 调用类型。支持 `http`, `socket`, `protobuf`。 |
| `target_config` | 是 | 目标配置对象。`http` 需配置 `url`, `method`；`socket` 需配置 `ip`, `port` 等。 |
| `params` | 否 | 参数定义字典。用于前端自动生成输入表单，支持设置 `default` 值。 |
| `assertions` | 否 | **默认断言规则**。Python 表达式列表，用于验证响应是否符合预期。 |
| `sample_return` | 否 | 示例返回值。用于前端展示结构，或在实际调用失败/Mock模式下作为兜底返回。 |

### 典型配置示例

#### 示例 1: 接入 HTTP 接口

```yaml
name: "用户下单接口"
call_type: "http"
description: "测试商城下单逻辑，验证余额扣除"
target_config:
  # 相对路径会自动拼接 config.yaml 中的 global_target_url，也可以写绝对路径
  url: "/api/order/create"
  method: "POST"
params:
  goods_id:
    type: "number"
    default: 10086
  count:
    type: "number"
    default: 1
assertions:
  - "response['code'] == 0"
  - "response['data']['order_status'] == 'pending'"
sample_return:
  code: 0
  message: "success"
  data:
    order_id: "ORD-9999"
```

#### 实例2: 接入Protobuf协议
需要编写少量 Python 代码定义协议结构。请见下说明。
具体文档说明: [PROTO_GUIDE.md](./documents/PROTO_GUIDE.md)

---
如需补充“抽卡/数值比拼”页面与接口细节，可继续说明需求。
