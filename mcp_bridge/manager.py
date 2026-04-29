from typing import Optional, Literal
from mcp_bridge.backends.base import BaseBackend
from mcp_bridge.backends.ssh import SSHBackend
from mcp_bridge.backends.docker import DockerBackend
from mcp_bridge.backends.wsl import WSLBackend

class NoBackendInitialized(Exception):
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
            raise ValueError(f"Unknown backend type: {backend_type}")

        self._backend_type = backend_type

    def execute(self, command: str) -> str:
        if not self._backend:
            raise NoBackendInitialized("Call init_session first")
        return self._backend.execute(command)

    def get_backend_type(self) -> Optional[Literal["ssh", "docker", "wsl"]]:
        return self._backend_type

    def close(self) -> None:
        if self._backend:
            self._backend.close()
            self._backend = None
            self._backend_type = None
