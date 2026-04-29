import docker
from remote_mcp.backends.base import BaseBackend

class DockerBackend(BaseBackend):
    def __init__(self, container: str):
        self.container = container
        self._client = docker.from_env()
        self._exec_id = None

    def execute(self, command: str) -> str:
        container = self._client.containers.get(self.container)
        exec_result = container.exec_run(
            cmd=command,
            stream=True,
            socket=True,
            demux=True,
        )
        output = b""
        while True:
            try:
                chunk = exec_result.output.read(1024)
                if not chunk:
                    break
                output += chunk
            except:
                break
        return output.decode("utf-8", errors="replace")

    def close(self) -> None:
        self._client.close()
