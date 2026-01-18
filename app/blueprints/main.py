from flask import Blueprint, render_template
from app.config import TITLE

# 创建 Main 蓝图
bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    """首页路由"""
    return render_template("index.html", title=TITLE)
