import sqlite3
import json
from flask import g, current_app
from app.config import DB_PATH, GAME_SERVER

class Database:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        初始化应用，注册资源释放回调
        """
        app.teardown_appcontext(self.close)

    @property
    def connection(self):
        """
        获取数据库连接。
        如果在当前应用上下文中已经存在连接，则直接返回；否则创建新连接。
        """
        if 'db' not in g:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
        return g.db

    def close(self, e=None):
        """关闭数据库连接"""
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def get_setting(self, key, default=None):
        """获取全局设置"""
        db = self.connection
        row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        """更新全局设置"""
        db = self.connection
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        db.commit()

    def init_db(self, app):
        """初始化数据库表结构和默认数据"""
        with app.app_context():
            conn = self.connection
            cur = conn.cursor()
            
            # 创建设置表
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )

            # 初始化默认设置
            cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('global_target_url', GAME_SERVER))
            
            # 创建历史记录表
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    action TEXT,  -- 简要描述或操作类型
                    protocol_name TEXT,
                    target_url TEXT,
                    request_body TEXT,  -- JSON
                    response_body TEXT, -- JSON
                    assertions TEXT,    -- JSON
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

            # 尝试为历史表添加新字段 (兼容旧数据库文件)
            new_cols = [
                ("protocol_name", "TEXT"),
                ("target_url", "TEXT"),
                ("request_body", "TEXT"),
                ("response_body", "TEXT"),
                ("assertions", "TEXT")
            ]
            for col_name, col_type in new_cols:
                try:
                    cur.execute(f"ALTER TABLE history ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()

db = Database()
