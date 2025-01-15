from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy

from routes import main
from utils import parse_app_config

app_config = parse_app_config("./conf/app.toml")

app = Flask(app_config.Host.Name)
app.secret_key = app_config.Host.Key

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{app_config.DB.Path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 禁用修改追踪，减少开销

db = SQLAlchemy()
db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(main)

if __name__ == "__main__":
    app.run(host='0.0.0.0',
            port=app_config.Host.Port,
            debug=False,
            threaded=True)

# tinyDB
# database = TinyDB(config.TinyDB.GpuRequestDatabaseSavePath,
#                   sort_keys=True,
#                   indent=4,
#                   separators=(',', ':'))

# user_info_database = database.table('user_info')
# docker_image_database = database.table('docker_images')
# gpu_request_database = database.table('gpu_request_database')

# flask blueprint
# from routes.gpu import gpu_bp
# from routes.container import container_bp
# from routes.user import user_bp

# app.register_blueprint(gpu_bp, url_prefix='/gpu')
# app.register_blueprint(container_bp, url_prefix='/container')
# app.register_blueprint(user_bp, url_prefix='/user')
