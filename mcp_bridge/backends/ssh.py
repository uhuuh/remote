import paramiko
from typing import Optional
import time
from mcp_bridge.backends.base import BaseBackend

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
        self._channel = None

    def _connect(self) -> None:
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

        self._channel = self._client.invoke_shell()
        self._channel.transport.set_keepalive(30)

    def execute(self, command: str) -> str:
        if not self._client:
            self._connect()

        self._channel.send(command + "\n")
        output = ""
        while True:
            if self._channel.recv_ready():
                data = self._channel.recv(1024).decode("utf-8")
                output += data
                if "$" in output or "#" in output:
                    break
            else:
                time.sleep(0.1)
        return output

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._channel = None
