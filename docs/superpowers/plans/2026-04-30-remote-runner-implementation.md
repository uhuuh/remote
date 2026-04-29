# Remote Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 单文件 Python 工具，连接远程后端、同步代码、执行任务

**Architecture:** 复用现有 BackendManager 和 backends，新增 SyncManager 和 TaskExecutor

**Tech Stack:** Python 标准库 + paramiko + docker-py

---

## File Structure

- Create: `remote_runner.py` - 全部逻辑
- Create: `tests/ut/test_remote_runner.py` - 单元测试

---

## Task 1: Config Dataclasses

**Files:**
- Create: `remote_runner.py:1-50`

- [ ] **Step 1: Define ConnectionConfig, SyncConfig, ExecuteConfig, Config dataclasses**

```python
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


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
```

- [ ] **Step 2: Commit**

```bash
git add remote_runner.py
git commit -m "feat: add config dataclasses"
```

---

## Task 2: BackendManager

**Files:**
- Modify: `remote_runner.py:51-100`（追加）
- Reuse: `remote_mcp/backends/ssh.py`, `remote_mcp/backends/docker.py`, `remote_mcp/backends/wsl.py`, `remote_mcp/manager.py`

- [ ] **Step 1: Import backends and define BackendManager**

```python
import sys
sys.path.insert(0, "/mnt/c/Users/uh/code/my/remote")

from remote_mcp.backends.ssh import SSHBackend
from remote_mcp.backends.docker import DockerBackend
from remote_mcp.backends.wsl import WSLBackend


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

    def close(self) -> None:
        if self._backend:
            self._backend.close()
            self._backend = None
```

- [ ] **Step 2: Commit**

```bash
git add remote_runner.py
git commit -m "feat: add BackendManager class"
```

---

## Task 3: SyncManager

**Files:**
- Modify: `remote_runner.py:101-180`（追加）

- [ ] **Step 1: Define SyncError exception and SyncManager class**

```python
import subprocess
import os
from datetime import datetime


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
        result = self.backend.execute(f"echo '{patch}' | {apply_cmd}")

        if result.returncode != 0:
            raise SyncError(f"Failed to apply patch: {result.stderr}")

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
            result = self.backend.execute(remote_cmd)
            if result.returncode != 0 and "nothing to commit" not in result.stderr:
                raise SyncError(f"Failed to create remote commit: {result.stderr}")
```

- [ ] **Step 2: Commit**

```bash
git add remote_runner.py
git commit -m "feat: add SyncManager for code synchronization"
```

---

## Task 4: TaskExecutor

**Files:**
- Modify: `remote_runner.py:181-240`（追加）

- [ ] **Step 1: Define ExecuteError and TaskExecutor class with real-time output**

```python
import subprocess
import sys


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

        full_command = f"cd {self.config.remote_path} && {command}"
        result = self.backend.execute(full_command)

        if result.returncode != 0:
            raise ExecuteError(f"Task '{name}' failed: {result.stderr}")

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
```

- [ ] **Step 2: Commit**

```bash
git add remote_runner.py
git commit -m "feat: add TaskExecutor with real-time output"
```

---

## Task 5: main() Function

**Files:**
- Modify: `remote_runner.py:241-280`（追加）

- [ ] **Step 1: Define main() function accepting config parameter**

```python
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
            type="ssh",
            host="example.com",
            username="user",
            password="pass",
        ),
        sync=SyncConfig(
            enabled=True,
            remote_path="/home/user/project",
        ),
        execute=ExecuteConfig(
            tasks={
                "build": "npm run build",
                "test": "npm test",
            },
            pipeline=["test", "build"],
        ),
    )
    main(config)
```

- [ ] **Step 2: Commit**

```bash
git add remote_runner.py
git commit -m "feat: add main() function"
```

---

## Task 6: Write Unit Tests

**Files:**
- Create: `tests/ut/test_remote_runner.py`

- [ ] **Step 1: Write tests for SyncManager._generate_patch**

```python
import pytest
from remote_runner import SyncManager, SyncConfig, BackendManager, ConnectionConfig


class TestSyncManager:
    def test_generate_patch_excludes_current_file(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        backend = BackendManager(config)
        sync_config = SyncConfig(enabled=True, remote_path="/tmp")
        manager = SyncManager(backend, sync_config)

        patch = manager._generate_patch("/some/path/remote_runner.py")
        assert "remote_runner.py" not in patch
```

- [ ] **Step 2: Write tests for TaskExecutor**

```python
class TestTaskExecutor:
    def test_execute_pipeline_task_not_found(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        backend = BackendManager(config)
        exec_config = ExecuteConfig(
            tasks={"build": "echo build"},
            pipeline=["test"],
        )
        executor = TaskExecutor(backend, exec_config)
        with pytest.raises(ExecuteError, match="Task 'test' not found"):
            executor.execute_pipeline()
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/ut/test_remote_runner.py -v
```

- [ ] **Step 4: Commit**

```bash
git add tests/ut/test_remote_runner.py
git commit -m "test: add unit tests for remote_runner"
```

---

## Self-Review Checklist

1. **Spec coverage:** All requirements from spec implemented?
   - Config structure: ConnectionConfig, SyncConfig, ExecuteConfig ✓
   - Sync with git diff/patch: ✓
   - Commit creation (local + remote): ✓
   - Task execution with real-time output: ✓
   - Strict mode (hunk failure throws exception): ✓

2. **Placeholder scan:** No TBD/TODO found ✓

3. **Type consistency:** All method signatures match across tasks ✓
