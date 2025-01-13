from typing import NamedTuple, Tuple

import pynvml
from pynvml_utils import nvidia_smi

GPUProcess = NamedTuple('GPUProcess', PID=int, memory=float)


class NvidiaGPU:

    def __init__(self) -> None:
        self.gpu_instance = nvidia_smi.getInstance()
        self.gpu_count = pynvml.nvmlDeviceGetCount()

    def gpu_name(self, gpu_id: int = 0) -> str:
        self.check_gpu_id(gpu_id)
        return self.gpuinstance.DeviceQuery()['gpu'][gpu_id]['product_name']

    def memory(self, gpu_id: int = 0) -> Tuple[str, str]:
        self.check_gpu_id(gpu_id)
        return str(int(self.gpuinstance.DeviceQuery('memory.used')['gpu'][gpu_id]['fb_memory_usage']['used'])), str(int(self.gpuinstance.DeviceQuery('memory.total')['gpu'][gpu_id]['fb_memory_usage']['total']))

    def check_gpu_id(self, gpu_id: int) -> None:
        assert isinstance(gpu_id, int) and gpu_id >= 0 and gpu_id < self.gpu_count

    def running_processes(self, gpu_id: int = 0) -> list[GPUProcess]:
        self.check_gpu_id(gpu_id)
        processes = self.gpuinstance.DeviceQuery('compute-apps')['gpu'][gpu_id]['processes']
        if processes is None:
            return []
        return [GPUProcess(int(_['pid']), float(_['used_memory'])) for _ in processes]

    def gpu_info(self) -> list[Tuple]:
        return [{'gpu_id': str(i), 'gputype': self.gpu_name(i), 'memory': '/'.join([*self.memory(i)]) + ' MB'} for i in range(self.gpu_count)]
