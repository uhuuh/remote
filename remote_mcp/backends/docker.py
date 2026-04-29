import subprocess
import time
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
        start_time = time.time()
        while True:
            chunk = process.stdout.read(1024)
            if chunk:
                output += chunk
            elif time.time() - start_time > 1:
                break
            else:
                time.sleep(0.1)

        process.wait()
        return output.decode("utf-8", errors="replace")

    def close(self) -> None:
        pass