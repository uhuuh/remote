from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
import subprocess
import os
import sys
from datetime import datetime

sys.path.insert(0, "/mnt/c/Users/uh/code/my/remote")

from remote_mcp.backends.ssh import SSHBackend
from remote_mcp.backends.docker import DockerBackend
from remote_mcp.backends.wsl import WSLBackend


@dataclass
class ConnectionConfig:
    type: Literal["ssh", "docker", "wsl"]
    host: Optional[str] = None
    port: int = 22
    username: Optional[str] = None
    password: Optional[str] = None
    container: Optional[str] = None


@dataclass
class SyncConfig:
    enabled: bool = False
    remote_path: str = ""


@dataclass
class ExecuteConfig:
    tasks: Dict[str, str] = field(default_factory=dict)
    pipeline: List[str] = field(default_factory=list)


@dataclass
class Config:
    connection: ConnectionConfig
    sync: SyncConfig = field(default_factory=SyncConfig)
    execute: ExecuteConfig = field(default_factory=ExecuteConfig)


class CommandResult:
    def __init__(self, stdout: str, stderr: str, returncode: int):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class BackendManager:
    def __init__(self, config: ConnectionConfig):
        self._backend = None
        self._config = config

    def _create_backend(self):
        cfg = self._config
        if cfg.type == "ssh":
            if not cfg.host or not cfg.username:
                raise ValueError("host and username are required for SSH backend")
            return SSHBackend(
                host=cfg.host,
                port=cfg.port,
                username=cfg.username,
                password=cfg.password,
            )
        elif cfg.type == "docker":
            if not cfg.container:
                raise ValueError("container is required for Docker backend")
            return DockerBackend(container=cfg.container)
        elif cfg.type == "wsl":
            return WSLBackend()
        else:
            raise ValueError(f"Unknown backend type: {cfg.type}")

    def execute(self, command: str) -> str:
        if not self._backend:
            self._backend = self._create_backend()
        return self._backend.execute(command)

    def execute_with_result(self, command: str) -> CommandResult:
        output = self.execute(f"{command}; echo EXIT_CODE=$?")
        if "EXIT_CODE=" in output:
            parts = output.rsplit("EXIT_CODE=", 1)
            stdout_part = parts[0].rstrip("\n")
            exit_code_str = parts[1].strip()
            try:
                returncode = int(exit_code_str)
            except ValueError:
                returncode = 1
            return CommandResult(stdout=stdout_part, stderr="", returncode=returncode)
        return CommandResult(stdout=output, stderr="", returncode=0)

    def close(self) -> None:
        if self._backend:
            self._backend.close()
            self._backend = None


class SyncError(Exception):
    pass


class SyncManager:
    def __init__(self, backend: BackendManager, config: SyncConfig):
        self.backend = backend
        self.config = config

    def sync(self, current_file: str) -> None:
        if not self.config.enabled:
            return

        patch = self._generate_patch(current_file)
        if not patch.strip():
            return

        self._apply_patch(patch)
        self._create_local_commit()
        self._create_remote_commit()

    def _generate_patch(self, current_file: str) -> str:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", ":!'" + current_file + "'"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(current_file)) or ".",
        )
        return result.stdout

    def _apply_patch(self, patch: str) -> None:
        if not patch.strip():
            return

        apply_cmd = f"cd {self.config.remote_path} && git apply -"
        result = self.backend.execute_with_result(f"echo '{patch}' | {apply_cmd}")

        if result.returncode != 0:
            raise SyncError(f"Failed to apply patch: {result.stderr if result.stderr else result.stdout}")

    def _create_local_commit(self) -> None:
        subprocess.run(["git", "add", "-A"], capture_output=True)
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        result = subprocess.run(
            ["git", "commit", "-m", f"chore: sync {timestamp}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "nothing to commit" not in result.stderr:
            raise SyncError(f"Failed to create local commit: {result.stderr}")

    def _create_remote_commit(self) -> None:
        config = self.backend._config
        if config.type == "ssh":
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            remote_cmd = f"cd {self.config.remote_path} && git add -A && git commit -m 'chore: sync {timestamp}'"
            result = self.backend.execute_with_result(remote_cmd)
            if result.returncode != 0 and "nothing to commit" not in result.stderr:
                raise SyncError(f"Failed to create remote commit: {result.stderr if result.stderr else result.stdout}")
