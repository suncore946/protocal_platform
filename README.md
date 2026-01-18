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
cd "e:\桌面\新建文件夹"
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
cd /path/to/project
python3 -m venv .venv
source .venv/bin/activate
```

## 3. 安装依赖

> 如果已使用 `environment.yml` 创建环境，可跳过此步骤。

```bash
pip install -r requirements.txt
```

## 4. 配置说明

- 配置文件：[config.yaml](config.yaml)
- 关键配置项：
  - `app.title`：页面标题
  - `app.secret_key`：Flask Session 密钥
  - `app.db_path`：SQLite 数据库文件
  - `app.log_file`：日志文件路径
- 初始协议数据可在 `protocol_defaults` 中维护

## 5. 初始化与启动（开发模式）

```bash
python app.py
```

启动后访问：

- [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 6. 目录结构

```text
.
├── app.py
├── config.yaml
├── requirements.txt
├── app.db              # 首次启动自动生成
├── logs/               # 日志目录（自动生成）
├── templates/
│   └── index.html
└── static/
    └── style.css
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
waitress-serve --listen=0.0.0.0:5000 app:app
```

## 9. 生产部署（Linux 示例：Gunicorn）

> 内网访问场景可直接使用 Gunicorn，无需反向代理。

### 安装 Gunicorn

```bash
pip install gunicorn
```

### 运行（示例）

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## 10. 数据库说明

- 使用 SQLite3，首次启动自动建表
- 协议表：`protocol`
- 操作历史表：`history`

## 11. 日志说明

- 使用 Loguru
- 日志文件位置：由 `config.yaml -> app.log_file` 指定
- 日志滚动：10MB 分片，保留 10 天

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
如需补充“抽卡/数值比拼”页面与接口细节，可继续说明需求。
