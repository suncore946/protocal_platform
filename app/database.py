import sqlite3
import json
from flask import g, current_app
from app.config import DB_PATH, PROTOCOL_DEFAULTS

def get_db():
    """
    获取数据库连接。
    如果在当前应用上下文中已经存在连接，则直接返回；否则创建新连接。
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_setting(key, default=None):
    """获取全局设置"""
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default

def set_setting(key, value):
    """更新全局设置"""
    db = get_db()
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()

def close_db(e=None):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """初始化数据库表结构和默认数据"""
    # 这里的 init_db 逻辑稍微调整，不依赖 Flask 上下文 g，而是直接连接
    # 或者在 app context 中运行
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        
        # 创建协议表
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS protocol (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                params_json TEXT,
                sample_return_json TEXT,
                call_type TEXT DEFAULT 'socket',
                target_config_json TEXT
            );
            """
        )

        # 尝试为旧表添加字段 (如果字段不存在)
        try:
            cur.execute("ALTER TABLE protocol ADD COLUMN call_type TEXT DEFAULT 'socket'")
        except sqlite3.OperationalError:
            pass # 字段可能已存在

        try:
            cur.execute("ALTER TABLE protocol ADD COLUMN target_config_json TEXT")
        except sqlite3.OperationalError:
            pass

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
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('global_target_url', 'http://game_backend.com'))
        
        # 创建历史记录表
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

        # 检查并更新默认协议数据
        # 遍历 PROTOCOL_DEFAULTS，如果不存在则插入
        for item in PROTOCOL_DEFAULTS:
            name = item.get("name")
            cur.execute("SELECT id FROM protocol WHERE name = ?", (name,))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO protocol (name, description, params_json, sample_return_json, call_type, target_config_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        item.get("description", ""),
                        json.dumps(item.get("params", {}), ensure_ascii=False),
                        json.dumps(item.get("sample_return", {}), ensure_ascii=False),
                        item.get("call_type", "socket"),
                        json.dumps(item.get("target_config", {}), ensure_ascii=False),
                    ),
                )
                current_app.logger.info(f"Inserted new default protocol: {name}")
        
        conn.commit()
