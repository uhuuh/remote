import subprocess
from remote_mcp.backends.base import BaseBackend

class DockerBackend(BaseBackend):
    def __init__(self, container: str):
        self.container = container

    def execute(self, command: str) -> str:
        result = subprocess.run(
            ["docker", "exec", self.container, "/bin/bash", "-l", "-c", command],
            capture_output=True,
            text=True,
        )
        return result.stdout + result.stderr

    def close(self) -> None:
        pass