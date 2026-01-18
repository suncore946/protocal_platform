import yaml
from pathlib import Path

# 计算项目根目录 (app/config.py -> app/ -> project_root)
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def _load_config():
    """加载配置文件的内部函数"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

# 加载配置 (模块级别单例)
_config_data = _load_config()

# 导出配置项
APP_CONFIG = _config_data.get("app", {})

# 路径配置
DB_PATH = BASE_DIR / APP_CONFIG.get("db_path", "app.db")
LOG_PATH = BASE_DIR / APP_CONFIG.get("log_file", "logs/app.log")
TEST_CASES_PATH = BASE_DIR / APP_CONFIG.get("test_cases_path", "test_cases")

# 应用配置
SECRET_KEY = APP_CONFIG.get("secret_key", "dev-secret-key")
TITLE = APP_CONFIG.get("title", "协议测试平台")
GAME_SERVER = APP_CONFIG.get("game_server", "http://game_backend.com")

def get_raw_config():
    """获取完整配置字典"""
    return _config_data
