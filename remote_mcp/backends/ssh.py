import paramiko
import time
from typing import Optional
from remote_mcp.backends.base import BaseBackend

class SSHBackend(BaseBackend):
    def __init__(
        self,
        host: str,
        username: str,
        port: int = 22,
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._client: Optional[paramiko.SSHClient] = None

    def _connect(self) -> None:
        if self._client is None:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                self._client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=None,
                    password=self.password,
                    look_for_keys=True,
                    allow_agent=True,
                )
            except paramiko.ssh_exception.SSHException:
                if self.password:
                    self._client.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                    )
                else:
                    raise

    def execute(self, command: str) -> str:
        self._connect()

        stdin, stdout, stderr = self._client.exec_command(
            f"/bin/bash -l -c '{command.replace('\'', '\'\"\'\'')}'"
        )

        output = ""
        start_time = time.time()
        while True:
            chunk = stdout.read(1024)
            if chunk:
                output += chunk.decode("utf-8")
            elif time.time() - start_time > 1:
                break
            else:
                time.sleep(0.1)

        error = stderr.read().decode("utf-8")
        return output + error

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None