from flask import Blueprint, jsonify
from models import User

# 创建一个蓝图
main = Blueprint('main', __name__)

@main.route('/')
def index():
    users = User.query.all()  # 查询所有用户
    return jsonify([{'id': user.id, 'username': user.username} for user in users])