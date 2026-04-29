from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
import subprocess
import os
import sys
import json
import paramiko
from datetime import datetime


@dataclass
class ConnectionConfig:
    type: Literal["ssh", "docker", "wsl"]
    host: Optional[str] = None
    port: int = 22
    username: Optional[str] = None
    password: Optional[str] = None
    container: Optional[str] = None
    remote_path: Optional[str] = None


@dataclass
class SyncConfig:
    """Configuration for code synchronization.

    Fields:
        sync: Whether to sync local changes to remote backend path.
        commit: Whether to create automatic commits on both local and remote.
                Requires sync=True to be set.
    """
    sync: bool = False
    commit: bool = False


@dataclass
class ExecuteConfig:
    tasks: Dict[str, str] = field(default_factory=dict)
    pipeline: List[str] = field(default_factory=list)


@dataclass
class Config:
    connection: ConnectionConfig
    sync: SyncConfig = field(default_factory=SyncConfig)
    execute: ExecuteConfig = field(default_factory=ExecuteConfig)


class SSHBackend:
    def __init__(self, host: str, username: str, port: int = 22, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._client = None

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
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        return output + error

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None


class DockerBackend:
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


class WSLBackend:
    def __init__(self):
        self.wsl_distro = None

    def _get_distro(self) -> str:
        if self.wsl_distro is None:
            result = subprocess.run(
                ["wsl", "-l", "--json"],
                capture_output=True,
                text=True,
            )
            distros = json.loads(result.stdout)
            if distros:
                self.wsl_distro = distros[0].get("name", "Ubuntu")
            else:
                self.wsl_distro = "Ubuntu"
        return self.wsl_distro

    def execute(self, command: str) -> str:
        distro = self._get_distro()
        result = subprocess.run(
            ["wsl", "-d", distro, "--", "/bin/bash", "-l", "-c", command],
            capture_output=True,
            text=True,
        )
        return result.stdout + result.stderr

    def close(self) -> None:
        pass


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


class ExecuteError(Exception):
    pass


class TaskExecutor:
    def __init__(self, backend: BackendManager, config: ExecuteConfig):
        self.backend = backend
        self.config = config

    def execute_pipeline(self) -> None:
        for task_name in self.config.pipeline:
            if task_name not in self.config.tasks:
                raise ExecuteError(f"Task '{task_name}' not found in tasks dict")
            command = self.config.tasks[task_name]
            self._execute_task(task_name, command)

    def _execute_task(self, name: str, command: str) -> None:
        print(f"\n=== Executing task: {name} ===")
        print(f"$ {command}")

        remote_path = self.backend._config.remote_path
        full_command = f"cd {remote_path} && {command}" if remote_path else command
        cfg = self.backend._config
        if cfg.type == "ssh":
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=cfg.host,
                port=cfg.port,
                username=cfg.username,
                password=cfg.password,
            )
            stdin, stdout, stderr = client.exec_command(
                f"/bin/bash -l -c '{full_command.replace('\'', '\'\"\'\'')}'"
            )
            for line in stdout:
                print(line, end="")
            for line in stderr:
                print(line, end="", file=sys.stderr)
            exit_code = stdout.channel.recv_exit_status()
            client.close()
            if exit_code != 0:
                raise ExecuteError(f"Task failed with exit code {exit_code}")
        elif cfg.type == "docker":
            proc = subprocess.Popen(
                ["docker", "exec", cfg.container, "/bin/bash", "-l", "-c", full_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in proc.stdout:
                print(line, end="")
            for line in proc.stderr:
                print(line, end="", file=sys.stderr)
            proc.wait()
            if proc.returncode != 0:
                raise ExecuteError(f"Task failed with exit code {proc.returncode}")
        elif cfg.type == "wsl":
            result = subprocess.run(
                ["wsl", "--", "/bin/bash", "-l", "-c", full_command],
                capture_output=True,
                text=True,
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            if result.returncode != 0:
                raise ExecuteError(f"Task failed with exit code {result.returncode}")


class SyncManager:
    def __init__(self, backend: BackendManager, config: SyncConfig):
        self.backend = backend
        self.config = config

    def sync(self, current_file: str) -> None:
        """Sync local changes to remote and optionally commit.

        Args:
            current_file: Path to the current file (used to exclude it from patch).

        Raises:
            SyncError: If commit=True but sync=False, or if remote_path is not set.
        """
        if not self.config.sync and not self.config.commit:
            return

        if self.config.commit and not self.config.sync:
            raise SyncError("commit=True requires sync=True")

        remote_path = self.backend._config.remote_path
        if not remote_path:
            raise SyncError("sync or commit requires remote_path")

        patch = self._generate_patch(current_file)
        if not patch.strip():
            return

        if self.config.sync:
            self._apply_patch(patch, remote_path)

        if self.config.commit:
            self._create_local_commit()
            self._create_remote_commit(remote_path)

    def _generate_patch(self, current_file: str) -> str:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", ":!'" + current_file + "'"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(current_file)) or ".",
        )
        return result.stdout

    def _apply_patch(self, patch: str, remote_path: str) -> None:
        if not patch.strip():
            return

        apply_cmd = f"cd {remote_path} && git apply -"
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

    def _create_remote_commit(self, remote_path: str) -> None:
        config = self.backend._config
        if config.type == "ssh":
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            remote_cmd = f"cd {remote_path} && git add -A && git commit -m 'chore: sync {timestamp}'"
            result = self.backend.execute_with_result(remote_cmd)
            if result.returncode != 0 and "nothing to commit" not in result.stderr:
                raise SyncError(f"Failed to create remote commit: {result.stderr if result.stderr else result.stdout}")


def main(config: Config) -> None:
    manager = BackendManager(config.connection)
    try:
        if config.sync.enabled:
            sync_mgr = SyncManager(manager, config.sync)
            sync_mgr.sync(__file__)

        executor = TaskExecutor(manager, config.execute)
        executor.execute_pipeline()
    finally:
        manager.close()


if __name__ == "__main__":
    config = Config(
        connection=ConnectionConfig(
            type="docker",
            container="verl",
            remote_path="/workspace",
        ),
        sync=SyncConfig(
            sync=True,
            commit=True,
        ),
        execute=ExecuteConfig(
            tasks={
                "test": "pwd",
            },
            pipeline=["test"],
        ),
    )
    main(config)
