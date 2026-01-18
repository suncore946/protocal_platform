import json
import random
import os
import yaml
from datetime import datetime
from flask import Blueprint, jsonify, request, session, current_app
from loguru import logger
from app.database import db
from app.connect import execute_protocol, log_protocol_history
from app.config import GAME_SERVER, TEST_CASES_PATH

# 创建 API 蓝图
bp = Blueprint('api', __name__, url_prefix='/api')

def get_test_cases_dir():
    return str(TEST_CASES_PATH)

def load_all_test_cases():
    """从 test_cases 目录加载所有 yaml 配置"""
    directory = get_test_cases_dir()
    cases = []
    
    if not os.path.exists(directory):
        logger.warning(f"Test cases directory not found: {directory}")
        return cases

    # 按文件名排序，保证 ID 相对稳定
    files = sorted([f for f in os.listdir(directory) if f.endswith('.yaml') or f.endswith('.yml')])
    
    for idx, filename in enumerate(files):
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if not isinstance(content, dict):
                    continue
                
                # 构造符合前端预期的结构
                cases.append({
                    "id": idx + 1,  # 动态生成 ID
                    "name": content.get("name", filename),
                    "description": content.get("description", ""),
                    "params": content.get("params", {}),
                    "sample_return": content.get("sample_return", {}),
                    "assertions": content.get("assertions", []),
                    "call_type": content.get("call_type", "http"),
                    "target_config": content.get("target_config", {}),
                    "test_cases": content.get("test_cases", []),
                    # 保留原始文件名以便调试或其他用途
                    "file_source": filename 
                })
        except Exception as e:
            logger.error(f"Failed to load test case {filename}: {e}")
            
    return cases

@bp.route("/protocols", methods=["GET"])
def get_protocols():
    """获取所有协议列表"""
    cases = load_all_test_cases()
    # 仅返回 ID 和 Name 给下拉列表使用
    return jsonify([{"id": c["id"], "name": c["name"]} for c in cases])

@bp.route("/doc", methods=["GET"])
def get_doc():
    """获取所有协议的清单列表"""
    cases = load_all_test_cases()
    return jsonify(cases)

@bp.route("/protocol/<int:protocol_id>", methods=["GET"])
def get_protocol_detail(protocol_id: int):
    """获取单个协议详细信息"""
    cases = load_all_test_cases()
    # 查找匹配 ID 的 case
    case = next((c for c in cases if c["id"] == protocol_id), None)
    
    if not case:
        return jsonify({"error": "protocol not found"}), 404
        
    return jsonify(case)


@bp.route("/protocol/<int:protocol_id>/call", methods=["POST"])
def call_protocol(protocol_id: int):
    """发起协议调用"""
    cases = load_all_test_cases()
    # 查找匹配 ID 的 case
    case = next((c for c in cases if c["id"] == protocol_id), None)
    
    if not case:
        return jsonify({"error": "protocol not found"}), 404

    payload = request.get_json(silent=True) or {}
    params = payload.get("params", {})
    # 优先使用 api 传入的断言，没传则使用配置中默认的
    assertions = payload.get("assertions")
    concurrency = int(payload.get("concurrency", 1))
    with_random = bool(payload.get("with_random", False))

    if assertions is None:
        assertions = case.get("assertions", [])

    base_return = case.get("sample_return", {})
    protocol_name = case.get("name", "Unknown Protocol")

    # 并发模拟函数
    def build_response(index: int):
        # 尝试调用后端具体逻辑
        # execute_protocol 现在支持传入 dict 类型的 target_config
        real_response = execute_protocol(case, params)
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

    # 尝试记录历史
    if session.get("username"):
        try:
             # 解析目标地址用于记录
            target_config = case.get("target_config", {})
            call_type = (case.get("call_type") or "socket").lower()
            if call_type == "http":
                # 再次获取 global setting 以拼凑完整 URL (仅做展示用)
                global_url = db.get_setting("global_target_url", GAME_SERVER)
                rel_url = target_config.get("url", "")
                from urllib.parse import urljoin
                target_info = urljoin(global_url, rel_url) if not rel_url.startswith("http") else rel_url
            else:
                target_info = f"{target_config.get('host')}:{target_config.get('port')}"
            
            # 记录所有结果（如果需要详细记录每一条，这里简化为只记录第一条的参数，但 result 放列表）
            # 或者按照原逻辑，这里将 results 作为 response_body 存入
            log_protocol_history(
                session.get("username"),
                protocol_name,
                target_info,
                params, 
                results if len(results) > 1 else results[0],
                assertions
            )
        except Exception as e:
            logger.error(f"Failed to log history: {e}")

    if concurrency == 1:
        return jsonify(results[0])
    else:
        return jsonify(results)

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
