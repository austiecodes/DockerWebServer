from typing import  NamedTuple
from pynvml_utils import nvidia_smi
from pynvml import  nvmlDeviceGetCount

GPUProcess = NamedTuple('GPUProcess', PID=int, memory=float)


class GPU:
    def __init__(self) -> None:
        self.gpu_instance = nvidia_smi.getInstance()
        self.gpu_count = nvmlDeviceGetCount()

    def gpu_name(self, gpu_id: int = 0) -> str:
        self.check_gpu_id(gpu_id)
        return self.gpu_instance.DeviceQuery()['gpu'][gpu_id]['product_name']

    def memory(self, gpu_id: int = 0) -> tuple[str, str]:
        self.check_gpu_id(gpu_id)
        return str(int(self.gpu_instance.DeviceQuery('memory.used')['gpu'][gpu_id]['fb_memory_usage']['used'])), str(int(self.gpu_instance.DeviceQuery('memory.total')['gpu'][gpu_id]['fb_memory_usage']['total']))

    def check_gpu_id(self, gpu_id: int) -> None:
        assert isinstance(gpu_id, int) and 0 <= gpu_id < self.gpu_count

    def running_processes(self, gpu_id: int = 0) -> list[GPUProcess]:
        self.check_gpu_id(gpu_id)
        processes = self.gpu_instance.DeviceQuery('compute-apps')['gpu'][gpu_id]['processes']
        if processes is None:
            return []
        return [GPUProcess(int(_['pid']), float(_['used_memory'])) for _ in processes]

    def gpu_info(self) -> list[dict[str, str]]:
        return [{'gpu_id': str(i), 'gpu_type': self.gpu_name(i), 'memory': '/'.join([*self.memory(i)]) + ' MB'} for i in range(self.gpu_count)]
