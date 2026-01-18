import json
import random
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from loguru import logger
from app.database import get_db, get_setting, set_setting
from app.connect import execute_protocol, log_protocol_test
from app.config import GAME_SERVER

# 创建 API 蓝图
bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route("/protocols", methods=["GET"])
def get_protocols():
    """获取所有协议列表"""
    db = get_db()
    rows = db.execute("SELECT id, name FROM protocol ORDER BY id ASC").fetchall()
    return jsonify([{"id": r["id"], "name": r["name"]} for r in rows])

@bp.route("/doc", methods=["GET"])
def get_doc():
    """获取所有协议的清单列表"""
    db = get_db()
    rows = db.execute("SELECT * FROM protocol ORDER BY id ASC").fetchall()
    
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "params": json.loads(row["params_json"] or "{}"),
            "sample_return": json.loads(row["sample_return_json"] or "{}"),
            "assertions": json.loads(row["assertions_json"] or "[]"),
            # 扩展配置信息回显
            "call_type": row["call_type"],
            "target_config": json.loads(row["target_config_json"] or "{}"),
        })
    return jsonify(results)

@bp.route("/protocol/<int:protocol_id>", methods=["GET"])
def get_protocol_detail(protocol_id: int):
    """获取单个协议详细信息"""
    db = get_db()
    row = db.execute("SELECT * FROM protocol WHERE id = ?", (protocol_id,)).fetchone()
    
    if not row:
        return jsonify({"error": "protocol not found"}), 404

    return jsonify(
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "params": json.loads(row["params_json"] or "{}"),
            "sample_return": json.loads(row["sample_return_json"] or "{}"),
            "assertions": json.loads(row["assertions_json"] or "[]"),
        }
    )

@bp.route("/protocol/<int:protocol_id>/call", methods=["POST"])
def call_protocol(protocol_id: int):
    """发起协议调用"""
    payload = request.get_json(silent=True) or {}
    params = payload.get("params", {})
    # 优先使用 api 传入的断言，没传则使用 db 中默认的
    assertions = payload.get("assertions")
    concurrency = int(payload.get("concurrency", 1))
    with_random = bool(payload.get("with_random", False))

    db = get_db()
    row = db.execute("SELECT * FROM protocol WHERE id = ?", (protocol_id,)).fetchone()
    
    if not row:
        return jsonify({"error": "protocol not found"}), 404
        
    if assertions is None:
        assertions = json.loads(row["assertions_json"] or "[]")

    base_return = json.loads(row["sample_return_json"] or "{}")
    protocol_name = row["name"]

    # 并发模拟函数
    def build_response(index: int):
        # 尝试调用后端具体逻辑
        real_response = execute_protocol(row, params)
        final_data = real_response if real_response else base_return
        
        # 执行自定义断言
        assertion_results = []
        if assertions:
            # 安全上下文：仅允许访问 response, params 以及基础类型
            context = {
                "response": final_data,
                "params": params,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict
            }
            for rule in assertions:
                try:
                    # 使用 eval 动态求值，禁用 __builtins__ 以提升安全性
                    is_pass = bool(eval(str(rule), {"__builtins__": None}, context))
                    assertion_results.append({"rule": rule, "status": "pass" if is_pass else "fail"})
                except Exception as e:
                    assertion_results.append({"rule": rule, "status": "error", "message": str(e)})

        resp = {
            "index": index,
            "request_params": params,
            "response": final_data,
            "assertions": assertion_results,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if with_random:
            resp["random"] = {
                "seed": random.randint(1, 999999),
                "value": random.random(),
            }
        return resp

    results = [build_response(i + 1) for i in range(max(concurrency, 1))]

    if session.get("username"):
        try:
             # 简单解析目标地址用于记录
            target_config = json.loads(row["target_config_json"] or "{}")
            call_type = (row["call_type"] or "socket").lower()
            if call_type == "http":
                # 再次获取 global setting 以拼凑完整 URL (仅做展示用)
                global_url = get_setting("global_target_url", GAME_SERVER)
                rel_url = target_config.get("url", "")
                from urllib.parse import urljoin
                target_info = urljoin(global_url, rel_url) if not rel_url.startswith("http") else rel_url
            else:
                target_info = f"{target_config.get('host')}:{target_config.get('port')}"

            log_protocol_test(
                username=session["username"],
                protocol_name=row["name"],
                target_url=target_info,
                request_params=params,
                response_data=results, # 记录所有并发结果
                assertions=assertions
            )
        except Exception as e:
            logger.error(f"Failed to log protocol test: {e}")

    return jsonify(
        {
            "protocol_id": protocol_id,
            "protocol_name": row["name"],
            "concurrency": max(concurrency, 1),
            "results": results,
        }
    )

@bp.route("/login", methods=["POST"])
def login():
    """模拟登录"""
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    
    if not username:
        return jsonify({"error": "username required"}), 400
        
    session["username"] = username
    logger.info(f"User login: {username}")
    return jsonify({"ok": True, "username": username})
