import subprocess
from remote_mcp.backends.base import BaseBackend

class DockerBackend(BaseBackend):
    def __init__(self, container: str):
        self.container = container

    def execute(self, command: str) -> str:
        process = subprocess.Popen(
            ["docker", "exec", "-i", self.container, "/bin/bash", "-l", "-c", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output = b""
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            output += chunk

        process.wait()
        return output.decode("utf-8", errors="replace")

    def close(self) -> None:
        pass