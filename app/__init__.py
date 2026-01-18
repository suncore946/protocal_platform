from flask import Flask
from loguru import logger
from app.config import LOG_PATH, SECRET_KEY, BASE_DIR
from app.database import db
from app.blueprints import main, api

def configure_logging():
    """配置 loguru 日志"""
    # 确保日志目录存在
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 添加文件日志 handler
    logger.add(
        LOG_PATH, 
        rotation="10 MB", 
        retention="10 days", 
        encoding="utf-8",
        level="INFO"
    )

def create_app():
    """Flask 应用工厂函数"""
    configure_logging()

    app = Flask(__name__, 
                template_folder=str(BASE_DIR / "templates"),
                static_folder=str(BASE_DIR / "static"))
    
    app.secret_key = SECRET_KEY

    # 注册数据库关闭函数
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)

    # 初始化数据库（在应用启动时检查）
    # 注意：在生产环境中，这通常通过单独的迁移脚本或 CLI 命令完成
    # 这里为了保持原有的便捷性，保留在启动时检查
    try:
        db.init_db(app)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    logger.info("Application started.")
    return app
