import subprocess
from remote_mcp.backends.base import BaseBackend

class WSLBackend(BaseBackend):
    def __init__(self):
        self.wsl_distro = None

    def _get_distro(self) -> str:
        if self.wsl_distro is None:
            result = subprocess.run(
                ["wsl", "-l", "--json"],
                capture_output=True,
                text=True,
            )
            import json
            distros = json.loads(result.stdout)
            if distros:
                self.wsl_distro = distros[0].get("name", "Ubuntu")
            else:
                self.wsl_distro = "Ubuntu"
        return self.wsl_distro

    def execute(self, command: str) -> str:
        distro = self._get_distro()
        process = subprocess.Popen(
            ["wsl", "-d", distro, "--", "/bin/bash", "-l", "-c", command],
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