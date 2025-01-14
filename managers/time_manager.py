import datetime
import os
import threading
import time


from docker_manager import DockerManager
from queue_manager import GPUQueueManager, GPURequest
from .mail_sender import EmailMessenger
from app.models.NvidiaGPU import NVIDIA_GPU
from app.utils import check_container


class TimeManager(threading.Thread):

    def __init__(self, nvidia_gpu: NVIDIA_GPU, docker_manager: DockerManager, gpu_queue_manager: GPUQueueManager, mail_manager: EmailMessenger):
        super().__init__()
        self.nvidia_gpu = nvidia_gpu
        self.docker_manager = docker_manager
        self.gpu_queue_manager = gpu_queue_manager
        self.mail_manager = mail_manager

    def run(self):
        while True:
            # 删除过时的请求
            changed = [False for _ in range(self.nvidia_gpu.gpucount)]
            next_item = [None for _ in range(self.nvidia_gpu.gpucount)]
            for idx, queue in enumerate(self.gpu_queue_manager.gpu_wait_queues):
                if len(queue) == 0:
                    continue
                q1: GPURequest = queue[0]
                if q1['end_time'] < datetime.datetime.now():
                    item: GPURequest = self.gpu_queue_manager.stop(idx)
                    changed[idx] = True
                    next_item[idx] = item

            # 检查并结束非法进程
            for gpuid in range(self.nvidia_gpu.gpucount):
                process = self.nvidia_gpu.running_processes(gpuid)
                process = [p for p in process if p.memory > 512]
                if len(process) == 0:
                    continue
                if len(self.gpu_queue_manager.gpu_wait_queues[gpuid]) == 0:
                    print(f'kill {[_.PID for _ in process]} 因为当前没有申请')
                    self.kill_process([_.PID for _ in process])
                    continue
                item: GPURequest = self.gpu_queue_manager.gpu_wait_queues[gpuid][0]
                user = item['user']
                containers = self.docker_manager.get_containers()
                containers_process = []
                for container in containers:
                    if check_container(container.name, user):
                        containers_process += [_.PID for _ in self.docker_manager.query_process(container.name)]

                for p in process:
                    if str(p.PID) not in containers_process:
                        print(f'kill {p.PID} 因为目标容器当中没有这个进程')
                        self.kill_process([p.PID])
            # 启动新进程
            for idx, queue in enumerate(self.gpu_queue_manager.gpu_wait_queues):
                if len(queue) == 0 or (not changed[idx]):
                    continue
                item: GPURequest = next_item[idx]
                if item['container'] is not None and item['cmd'] is not None:
                    self.docker_manager.run_exec(item['container'], item['cmd'], item['user'])
                    if item['user'] in self.mail_manager.user_email:
                        self.mail_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}GPU可用通知", f"你在服务器上预约的GPU已经可以使用,你托管的启动命令已经启动。你申请的使用时长为{item['duration']}小时,可用时间为{item['start_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}到{item['end_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}.", item['user'])
                else:
                    if item['user'] in self.mail_manager.user_email:
                        self.mail_manager.send(f"{datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S %f' )}GPU可用通知", f"你在服务器上预约的GPU已经可以使用,请尽快登录容器完成实验。你申请的使用时长为{item['duration']}小时,可用时间为{item['start_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}到{item['end_time'].strftime( '%Y-%m-%d %H:%M:%S %f' )}.", item['user'])

            # 发送队列中的邮件
            while len(self.mail_manager.send_queue) != 0:
                time.sleep(1)
                self.mail_manager._send()

            time.sleep(20)

    def kill_process(self, process: list[int]):
        for pid in process:
            os.system(f'kill -9 {pid}')
