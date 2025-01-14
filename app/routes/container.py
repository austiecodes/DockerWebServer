import json
import datetime
import json
import os
import time

from flask import Flask, app, jsonify, redirect, request
from tinydb import Query, TinyDB

import app.config as config
from app.managers import DockerManager,GPUQueueManager, GPURequest, EmailMessenger ,TimeManager
from app.models import NVIDIA_GPU

from app.utils import check_password,check_container
from flask import Blueprint, request

container_bp = Blueprint('container', __name__)

@app.route('/containermanager/imagelist')
def imagelist():
    r = []
    for image in docker_image_database.all():
        r.append({"imagename": image['show_name'], "env": image['env_description'], "useguide": image['use_description']})
    return json.dumps(r)


@app.route('/containermanager/mycontainer')
def mycontainer():
    uname = request.cookies.get('uname')
    containers = docker_manager.all_containers
    # print(containers)
    r = []
    for container in containers:
        if check_container(container.name, uname):
            r.append({"containername": container.name, "imagename": image_name_dict[container.image] if container.image in image_name_dict else "Unknown", "status": container.status, "ports": '|'.join([f"{port['container_port']}->{port['host_port']}" for port in container.ports])})

    return json.dumps(r)


@app.route('/containermanager/applyforcontainer', methods=['POST'])
def applyforcontainer():
    attrs = request.json
    uname = request.cookies.get('uname')
    imagename = attrs['imagename']
    ports = attrs['ports']
    containers = docker_manager.all_containers
    ports_used = []
    # 查找该用户已有的容器
    r = []
    for container in containers:
        if check_container(container.name, uname):
            r.append(container.name)
        # 统计在docker系统当中已经被占用的端口
        ports_used += [_['host_port'] for _ in container.ports]
    # 选择不存在的容器名
    for i in ['a', 'b', 'c']:
        if f'{uname}_{i}' not in r:
            containername = f'{uname}_{i}'
            break
    # 处理额外端口
    if ports is not None and ports != '':
        ports = [int(_) for _ in ports.split('|')]
    else:
        ports = []
    # 查找对应的镜像信息
    image = docker_image_database.search(query.show_name == imagename)[0]
    # 获取镜像的默认端口信息
    default_ports = image['default_ports']
    image: str = image['name']
    # 处理创建容器需要的文件
    if os.path.exists(f'data/user/{uname}/{containername}'):  # 如果存在旧文件则删除
        os.system(f'rm -r data/user/{uname}/{containername}')
    os.makedirs(f'data/user/{uname}/{containername}')
    # 拷贝四个文件
    os.system(f'cp data/image/{image}/group data/user/{uname}/{containername}')
    os.system(f'cp data/image/{image}/shadow data/user/{uname}/{containername}')
    os.system(f'cp data/image/{image}/passwd data/user/{uname}/{containername}')
    os.system(f'cp data/image/{image}/sudoers data/user/{uname}/{containername}')
    time.sleep(0.05)
    # 写入用户信息
    os.system(f'echo {uname}:x:$(id -g {uname}) >> data/user/{uname}/{containername}/group')  # 添加用户组
    os.system(f'echo $(cat /etc/shadow | grep {uname}:) >> data/user/{uname}/{containername}/shadow')  # 设置密码
    os.system(f'echo $(cat /etc/passwd | grep {uname}:) >> data/user/{uname}/{containername}/passwd')  # 设置用户
    os.system(f'echo "{uname} ALL=(ALL:ALL) NOPASSWD: ALL" >> data/user/{uname}/{containername}/sudoers')  # 设置sudo权限
    # 将以上文件的创建者设置为root
    os.system(f'chown -R root:root data/user/{uname}/{containername}/*')
    # 拷贝启动脚本并将所有者设置为当前用户
    os.system(f'cp data/image/{image}/start.sh data/user/{uname}/{containername}')
    os.system(f'chown {uname}:{uname} data/user/{uname}/{containername}/start.sh')
    # 如果没有workspace文件夹则创建
    if not os.path.exists(f'/data/{uname}/workspace'):
        os.makedirs(f'/data/{uname}/workspace')
        os.system(f'chown -R {uname} /data/{uname}/workspace')
    # 所有路径转化为绝对路径
    group_path = os.path.abspath(f'data/user/{uname}/{containername}/group')
    shadow_path = os.path.abspath(f'data/user/{uname}/{containername}/shadow')
    passwd_path = os.path.abspath(f'data/user/{uname}/{containername}/passwd')
    sudoers_path = os.path.abspath(f'data/user/{uname}/{containername}/sudoers')
    workspace = os.path.abspath(f'/data/{uname}/workspace')
    start_file = os.path.abspath(f'data/user/{uname}/{containername}/start.sh')
    # 所有需要映射的端口
    for port in default_ports:
        if port not in ports:
            ports.append(port)
    # 查找未使用的主机端口
    host_ports = []
    for i in range(1000):
        if i + 10000 not in ports_used:
            host_ports.append(i + 10000)
        if len(host_ports) == len(ports):
            break
    # 设置文件映射
    volumes = {}
    volumes[group_path] = {'bind': '/etc/group', 'mode': 'ro'}
    volumes[shadow_path] = {'bind': '/etc/shadow', 'mode': 'ro'}
    volumes[passwd_path] = {'bind': '/etc/passwd', 'mode': 'ro'}
    volumes[sudoers_path] = {'bind': '/etc/sudoers', 'mode': 'ro'}
    volumes[workspace] = {'bind': f'/home/{uname}/workspace', 'mode': 'rw'}
    volumes[start_file] = {'bind': f'/home/{uname}/start.sh', 'mode': 'ro'}
    # 设置端口映射
    ports_ = {}
    for p, q in zip(ports, host_ports):
        ports_[f'{p}/tcp'] = q
    # 容器内用户的uid
    uid = int(os.popen(f'id -u {uname}').read().replace('/n', ''))
    # 创建容器
    docker_manager.image_instantiation(containername, uid, image, '4g', volumes, f'/home/{uname}/workspace', ports_, None, cmd=f'bash /home/{uname}/start.sh')
    return "容器创建完成."


@app.route('/containermanager/containeropt', methods=['POST'])
def containeropt():
    # 执行容器启动/停止/删除操作
    attrs = request.json
    containername = attrs['containername']
    opt = attrs['opt']
    if opt == 'stop':
        docker_manager.stop_container(containername)
    if opt == 'start':
        docker_manager.start_container(containername)
    if opt == 'remove':
        docker_manager.remove_container(containername)
    return "容器操作完成,请等待5s再进行操作."