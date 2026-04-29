import subprocess
from remote_mcp.backends.base import BaseBackend

class WSLBackend(BaseBackend):
    def __init__(self):
        self._process = None

    def _ensure_shell(self) -> None:
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(
                ["wsl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

    def execute(self, command: str) -> str:
        self._ensure_shell()
        self._process.stdin.write(command + "\n")
        self._process.stdin.flush()
        output = ""
        while True:
            line = self._process.stdout.readline()
            if not line:
                break
            output += line
            if "$" in line or "#" in line:
                break
        return output

    def close(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None
