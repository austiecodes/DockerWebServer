from flask import Blueprint, app, request, jsonify


from flask import Flask, jsonify, redirect, request
from tinydb import Query, TinyDB

import app.config as config
from app.managers import DockerManager,GPUQueueManager, GPURequest, EmailMessenger ,TimeManager
from app.models import NVIDIA_GPU

from app.utils import check_password,check_container

user_bp = Blueprint('user', __name__)

@app.route('/')
def index():
    if 'uname' in request.cookies:  # cookie中有uname项, 说明已经登录
        return redirect('/static/userPageNew.html')  # 跳转到用户页面
    else:
        return redirect('/login')  # 跳转到登录页面


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        if request.form['key'] == 'login':
            user_name = request.form.get('account')
            passward = request.form.get('password')
            hold_login = request.form.get('holdlogin')
            if check_password(user_name, passward):
                resp = redirect('/')
                if hold_login == 'True':
                    resp.set_cookie('uname', user_name, 60 * 60 * 24 * 30 * 36)
                else:
                    resp.set_cookie('uname', user_name, 60 * 60)
                return resp
            else:
                # flash("该用户名不存在或密码错误")
                return redirect('/login')
    return redirect('/static/login.html')

@app.route('/checkpasswd', methods=["POST"])
def checkpasswd():
    uname = request.cookies.get('uname')
    passwd = request.json['password']
    if check_password(uname, passwd):
        return 'True'
    else:
        return 'False'



@app.route('/setting/loademail')
def loademail():
    uname = request.cookies.get('uname')
    user = user_info_database.search(query.user == uname)
    if len(user) == 0:
        return jsonify({}), 404
    if user[0]['email'] is None:
        return jsonify({}), 404
    return user[0]['email'], 200


@app.route('/setting/setemail', methods=['POST'])
def setemail():
    uname = request.cookies.get('uname')
    query = user_info_database.search(query.name == uname)
    email = request.json['email']
    if len(query) == 0:
        user_info_database.insert({'user': uname, 'name': None, 'email': email})
    else:
        query[0]['email'] = email
    neteasy_email_manager.user_email[uname] = email
    return "成功"


@app.route('/setting/loadname')
def loadname():
    uname = request.cookies.get('uname')
    user = user_info_database.search(query.user == uname)
    if len(user) == 0 or user[0]['name'] is None:
        return jsonify({}), 404
    return user[0]['name'], 200


@app.route('/setting/setname', methods=['POST'])
def setname():
    uname = request.cookies.get('uname')
    user = user_info_database.search(query.user == uname)
    name = request.json['name']
    user2name[uname] = name
    if len(user) == 0:
        user_info_database.insert({'user': uname, 'name': name, 'email': None})
    else:
        user[0]['name'] = name
    return "成功"


@app.route('/setting/suggest', methods=['POST'])
def suggest():
    uname = request.cookies.get('uname')
    content = request.json['content']
    neteasy_email_manager.send(uname + "的留言", content, 'administrator')
    return "提交成功!"


@app.route('/setting/addimages', methods=['GET', 'POST'])
def addimages():
    if request.method == 'GET':
        return ''
    image = request.json['image']
    passwd = request.json['passwd']
    if passwd != config.administrator_passwd:
        return "密码错误"
    docker_image_database.insert(image)
    image_name_dict[image['name']] = image['show_name']
    return "添加成功"


@app.route('/setting/quit')
def quit():
    uname = request.cookies.get('uname')
    resp = redirect('/')
    resp.set_cookie('uname', uname, 0)
    return resp

@app.route('/setting/backendstatus')
def backendstatus():
    if time_manager.is_alive():
        return "true"
    else:
        return "false"