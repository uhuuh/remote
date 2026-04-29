from typing import Optional, Literal
from remote_mcp.backends.base import BaseBackend
from remote_mcp.backends.ssh import SSHBackend
from remote_mcp.backends.docker import DockerBackend
from remote_mcp.backends.wsl import WSLBackend

class NoSessionError(Exception):
    pass

class ConnectionError(Exception):
    pass

class ConfigError(Exception):
    pass

class BackendManager:
    def __init__(self):
        self._backend: Optional[BaseBackend] = None
        self._backend_type: Optional[Literal["ssh", "docker", "wsl"]] = None

    def init(self, backend_type: Literal["ssh", "docker", "wsl"], **kwargs) -> None:
        if self._backend:
            self._backend.close()

        if backend_type == "ssh":
            self._backend = SSHBackend(**kwargs)
        elif backend_type == "docker":
            self._backend = DockerBackend(**kwargs)
        elif backend_type == "wsl":
            self._backend = WSLBackend()
        else:
            raise ConfigError(f"Unknown backend type: {backend_type}")

        self._backend_type = backend_type

    def execute(self, command: str) -> str:
        if not self._backend:
            raise NoSessionError("请先调用 init_session 初始化会话")
        return self._backend.execute(command)

    def get_backend_type(self) -> Optional[Literal["ssh", "docker", "wsl"]]:
        return self._backend_type

    def close(self) -> None:
        if self._backend:
            self._backend.close()
            self._backend = None
            self._backend_type = None
