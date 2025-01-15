import datetime
import json
import os
import time

from flask import Blueprint, Flask, app, jsonify, redirect, request
from tinydb import Query, TinyDB

from managers import (DockerManager, EmailMessenger, GPUQueueManager,
                          GPURequest, TimeManager)
from models import NVIDIA_GPU
from app.utils import check_container, check_password

gpu_bp = Blueprint('gpu', __name__)

# 初始化管理器等（根据您的需求调整）
nvidia_gpu = NVIDIA_GPU()
gpu_queue_manager = GPUQueueManager(nvidia_gpu.gpucount)
docker_manager = DockerManager()

@app.route('/gpumanager/gpuinfo')
def gpuinfo():
    gpu_info = nvidia_gpu.gpu_info()  # 获取GPU信息
    for i in range(nvidia_gpu.gpucount):
        ginfo = gpu_info[i]
        waitlist = gpu_queue_manager.gpu_wait_queues[i]
        if len(waitlist) == 0:
            ginfo['currentuser'] = '无'
            ginfo['waittime'] = '无'
        else:
            ginfo['currentuser'] = user2name[waitlist[0]['user']] if waitlist[0]['user'] in user2name else waitlist[0]['user']
            d: datetime.timedelta = waitlist[-1]['end_time'] - datetime.datetime.now()  # 计算等待时间
            ginfo['waittime'] = f'{int(d.total_seconds()//3600)}小时{int((d.total_seconds()%3600)//60)}分钟'
    return json.dumps(gpu_info)


@app.route('/gpumanager/waitlist')
def waitlist():
    reslist = []
    for idx, queue in enumerate(gpu_queue_manager.gpu_wait_queues):
        for item in queue:
            dbid = item['id']
            dbitem = gpu_request_database.search(query.id == dbid)[0]
            reslist.append({'user': user2name[item['user']] if item['user'] in user2name else item['user'], 'gpuid': idx, 'duration': item['duration'], 'reason': dbitem['reason'], 'container': '无' if item['container'] is None else item['container'], 'cmd': '无' if item['cmd'] is None else item['cmd']})
    return json.dumps(reslist)


@app.route('/gpumanager/currentitem')
def currentitem():
    r = []  # retuen list
    uname = request.cookies.get('uname')
    for idx, queue in enumerate(gpu_queue_manager.gpu_wait_queues):
        for item in queue:
            if item['user'] == uname:
                r_dict = {'gpuid': idx, 'duration': item['duration']}
                if item['start_time'] < datetime.datetime.now():
                    r_dict['status'] = '正在使用'
                    d: datetime.timedelta = item['end_time'] - datetime.datetime.now()
                    r_dict['timeinfo'] = f'{int(d.total_seconds()//3600)}小时{int((d.total_seconds()%3600)//60)}分钟后结束'
                else:
                    r_dict['status'] = '排队等待'
                    d = item['start_time'] - datetime.datetime.now()
                    r_dict['timeinfo'] = f'{int(d.total_seconds()//3600)}小时{int((d.total_seconds()%3600)//60)}分钟后可用'
                r.append(r_dict)
    return json.dumps(r)


@app.route('/gpumanager/applyforgpu', methods=['POST'])
def applyforgpu():
    attrs = request.json
    uname = request.cookies.get('uname')
    id = len(gpu_request_database.all())
    container, cmd = attrs['container'], attrs['cmd']
    if container == "选择容器" or cmd == '':  # 没有设置容器和命令
        container = None
        cmd = None
    item: GPURequest = gpu_queue_manager.new_item(id, int(attrs['gpuid']), uname, int(attrs['duration']), container, cmd)
    gpu_request_database.insert({'id': id, 'user': uname, 'gpuid': int(attrs['gpuid']), 'duration': int(attrs['duration']), 'reason': attrs['reason'], 'container': container, 'cmd': cmd})
    r_str = '申请成功!'
    start_time: datetime.datetime = item['start_time']
    if start_time < datetime.datetime.now():
        r_str += '你获得GPU使用权限.'
        if container is not None and cmd is not None:
            docker_manager.run_exec(item['container'], item['cmd'], item['user'])
            r_str += '你托管的指令已经执行.'
        else:
            r_str += '请抓紧时间利用GPU.'
    else:
        r_str += f'正在排队等待GPU,GPU预计将于{start_time.year}年{start_time.month}月{start_time.day}日{start_time.hour}时{start_time.minute}分可用.'
        if container is not None and cmd is not None:
            r_str += '你托管的指令将在GPU可用时自动执行.'
        else:
            r_str += '你没有托管指令,系统将在GPU可用时通过电子邮件通知.'
    return r_str


@app.route('/gpumanager/stopearlycontainer')
def stopearlycontainer():
    user = request.args.get('user')
    ip_addr = request.remote_addr
    containers = docker_manager.get_containers()
    for container in containers:
        if check_container(container.name, user):
            if container.ip == ip_addr:
                for idx, item in enumerate(gpu_queue_manager.current_item()):
                    if item is not None and item['user'] == user:
                        if item['user'] in neteasy_email_manager.user_email:
                            neteasy_email_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}程序运行完成通知", "你运行的实验进程已经运行完成，GPU不再可用，再次使用请重新申请。", item['user'])
                        item: GPURequest = gpu_queue_manager.stop(idx)
                        if item is not None:
                            if item['container'] is not None and item['cmd'] is not None:
                                docker_manager.run_exec(item['container'], item['cmd'], item['user'])
                                if item['user'] in neteasy_email_manager.user_email:
                                    neteasy_email_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}GPU可用通知", f"你在服务器上预约的GPU已经可以使用,你托管的启动命令已经启动。你申请的使用时长为{item['duration']}小时,可用时间为{item['start_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}到{item['end_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}.", item['user'])
                            else:
                                if item['user'] in neteasy_email_manager.user_email:
                                    neteasy_email_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}GPU可用通知", f"你在服务器上预约的GPU已经可以使用,请尽快登录容器完成实验。你申请的使用时长为{item['duration']}小时,可用时间为{item['start_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}到{item['end_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}.", item['user'])
                        return "当前任务已结束"
    return "IP 验证错误"


@app.route('/gpumanager/stopearlyweb', methods=['POST'])
def stopearlyweb():
    attrs = request.json
    gpuid = int(attrs['gpuid'])
    # print(gpuid)
    uname = request.cookies.get('uname')
    if len(gpu_queue_manager.gpu_wait_queues[gpuid]) == 0 or gpu_queue_manager.gpu_wait_queues[gpuid][0]['user'] != uname:
        return "消息过时，请刷新网页！"
    item: GPURequest = gpu_queue_manager.stop(gpuid)
    if item is not None:
        if item['container'] is not None and item['cmd'] is not None:
            docker_manager.run_exec(item['container'], item['cmd'], item['user'])
            if item['user'] in neteasy_email_manager.user_email:
                neteasy_email_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}GPU可用通知", f"你在服务器上预约的GPU已经可以使用,你托管的启动命令已经启动。你申请的使用时长为{item['duration']}小时,可用时间为{item['start_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}到{item['end_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}.", item['user'])
        else:
            if item['user'] in neteasy_email_manager.user_email:
                neteasy_email_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}GPU可用通知", f"你在服务器上预约的GPU已经可以使用,请尽快登录容器完成实验。你申请的使用时长为{item['duration']}小时,可用时间为{item['start_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}到{item['end_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}.", item['user'])
    return "当前任务已结束"


@app.route('/gpumanager/cancleapplyfor', methods=['POST'])
def cancleapplyfor():
    attrs = request.json
    uname = request.cookies.get('uname')
    # print(len(gpu_request_database))
    gpuid = int(attrs['gpuid'])
    # print(gpuid)
    queue = gpu_queue_manager.gpu_wait_queues[gpuid]
    for i in range(len(queue)):
        if queue[i]['user'] == uname:
            queue.pop(i)
            break
    return "申请已经撤销。"


@app.route('/gpumanager/requesthistory')
def requesthistory():
    uname = request.cookies.get('uname')
    r = []
    for item in gpu_request_database.search(query.user == uname):
        r.append({"gpuid": item['gpuid'], "duration": item['duration'], "reason": item['reason'], "cmd": item['cmd']})
    r = remove_reapeted_request(r)
    return json.dumps(r[::-1])