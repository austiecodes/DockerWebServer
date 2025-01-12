import os
from typing import NamedTuple,List
import docker

DockerProcess = NamedTuple('DockerProcess', PID=int, PPID=int, size=float, cmd=str)
DockerContainer = NamedTuple('DockerContainer', name=str, image=str, ports=dict, volume=list, ip=str, status=str)


class DockerManager:

    def __init__(self) -> None:
        self.docker_client = docker.from_env()

    @property
    def images(self) -> List[str]:
        return [str(image)[9:-2] for image in self.docker_client.images.list()]

    @property
    def running_containers(self) -> List[DockerContainer]:
        return self.get_containers()

    @property
    def all_containers(self) -> List[DockerContainer]:
        return self.get_containers(True)

    def get_containers(self, get_all: bool = False) -> List[DockerContainer]:

        def get_port_binding(attrs):
            port_bindings = attrs['HostConfig']['PortBindings']
            return [{'container_port': int(key.split('/')[0]), 'host_port': int(port_bindings[key][0]['HostPort'])} for key in port_bindings]

        return [
            DockerContainer(container.name,
                            str(container.image)[9:-2], get_port_binding(container.attrs), container.attrs['HostConfig']['Binds'], container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress'], 'running' if container.attrs['State']['Running'] else 'stopped')
            for container in self.docker_client.containers.list(get_all)
        ]

    def image_instantiation(self, container_name: str, user: str, image: str, shm_size: str, volume: List[str], working_dir: str, ports: dict, environment: dict , cmd: str  = None) -> None:
        """
        Args:
            container_name:容器名 e.g. 'my_container'
            user: name of user
            image:镜像 e.g. 'ubuntu:latest'
            shm_size:共享内存大小 e.g. '2g'
            volume:目录映射列表(主机:容器) e.g. ['/home/A:/root/A','/home/B:/root/C'] 
            working_dir:默认工作目录 e.g. '/root/working_dir'
            ports:端口映射 (容器:主机) e.g. {'22/tcp':1234,'5555/tcp':6660} or {'22/tcp':[1234,12345]}
            environment: 环境变量 e.g. ['SERVER_USER=tom']
            cmd:启动时命令 e.g. 'bash'
        """
        try:
            self.docker_client.containers.create(image=image, user=user, command=cmd, working_dir=working_dir, device_requests=[docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])], volumes=volume, shm_size=shm_size, ports=ports, name=container_name, environment=environment)
        except:
            ...

    def stop_container(self, container_name: str) -> None:
        self.find_container(container_name).stop()

    def start_container(self, container_name: str) -> None:
        self.find_container(container_name).start()

    def remove_container(self, container_name: str) -> None:
        self.find_container(container_name).remove(force=True)

    def find_container(self, container_name: str):
        return self.docker_client.containers.get(container_name)

    def run_exec(self, container_name: str, cmd: str,user:str):
        try:
            uid = int(os.popen(f'id -u {user}').read().replace('/n',''))
            self.find_container(container_name).exec_run(cmd, False,False,user=str(uid))
        except:
            ...

    def query_process(self, container_name: str) -> List[DockerProcess]:
        """return List of [pid,size(kb),cmd]
        """
        processes = self.find_container(container_name).top(ps_args='-eo pid,ppid,size,cmd')['Processes']
        return [DockerProcess(*_) for _ in processes]