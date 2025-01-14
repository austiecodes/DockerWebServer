import os

from flask import Flask
from tinydb import TinyDB

import app.config as config
from app.routes.gpu import gpu_bp  # 导入 GPU 路由蓝图
from app.routes.container import container_bp  # 导入容器路由蓝图
from app.routes.user import user_bp  # 导入用户路由蓝图

# 初始化数据库和应用程序
database = TinyDB('data/database/database.json', sort_keys=True, indent=4, separators=(',', ': '))
app = Flask("DSM")
app.secret_key = 'DSM'

# 加载数据库表格
user_info_database = database.table('user_info')
docker_image_database = database.table('docker_images')
gpu_request_database = database.table('gpu_request_database')

# 注册蓝图
app.register_blueprint(gpu_bp, url_prefix='/gpumanager')
app.register_blueprint(container_bp, url_prefix='/containermanager')
app.register_blueprint(user_bp, url_prefix='/setting')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=config.serverPort, debug=False, threaded=True)