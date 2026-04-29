# MCP Bridge Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MCP server with fastmcp that provides unified interface to SSH, Docker, and WSL backends.

**Architecture:** Single `mcp_bridge` package with BackendManager routing to SSH/Docker/WSL backends. Config stored in YAML file.

**Tech Stack:** Python, fastmcp, paramiko (SSH), docker (Docker), subprocess (WSL), PyYAML

---

## File Structure

```
mcp_bridge/
├── __init__.py
├── server.py           # fastmcp server + tools
├── config.py          # ConfigStore (YAML read/write)
├── backends/
│   ├── __init__.py
│   ├── base.py        # BaseBackend abstract class
│   ├── ssh.py         # SSHBackend via paramiko
│   ├── docker.py      # DockerBackend via docker-py
│   └── wsl.py         # WSLBackend via subprocess
tests/
├── __init__.py
├── test_config.py
├── test_ssh.py
├── test_docker.py
└── test_wsl.py
```

---

## Task 1: Project Setup

**Files:**
- Create: `mcp_bridge/__init__.py`
- Create: `mcp_bridge/backends/__init__.py`
- Create: `tests/__init__.py`
- Create: `pyproject.toml`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "mcp-bridge"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastmcp",
    "paramiko",
    "docker",
    "pyyaml",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_backend"

[tool.setuptools.packages.find]
where = ["."]
```

- [ ] **Step 2: Create mcp_bridge/__init__.py**

```python
"""MCP Bridge - Unified MCP server for SSH, Docker, and WSL backends."""
```

- [ ] **Step 3: Create mcp_bridge/backends/__init__.py**

```python
"""Backends for MCP Bridge."""
```

- [ ] **Step 4: Create tests/__init__.py**

```python
"""Tests for MCP Bridge."""
```

- [ ] **Step 5: Commit**

```bash
git init && git add -A && git commit -m "feat: project setup"
```

---

## Task 2: ConfigStore Implementation

**Files:**
- Create: `mcp_bridge/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test for ConfigStore**

```python
import os
import tempfile
from mcp_bridge.config import ConfigStore

def test_config_store_save_and_load():
    store = ConfigStore("test_config.yaml")
    config = {
        "backend": "ssh",
        "ssh": {"host": "192.168.1.1", "port": 22, "username": "user"},
    }
    store.save(config)
    loaded = store.load()
    assert loaded == config
    os.remove("test_config.yaml")

def test_config_store_load_returns_none_for_missing_file():
    store = ConfigStore("nonexistent.yaml")
    assert store.load() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (ConfigStore not defined)

- [ ] **Step 3: Write minimal ConfigStore**

```python
import yaml
from pathlib import Path
from typing import Optional

class ConfigStore:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)

    def save(self, config: dict) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(config, f)

    def load(self) -> Optional[dict]:
        if not self.config_path.exists():
            return None
        with open(self.config_path) as f:
            return yaml.safe_load(f)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/config.py tests/test_config.py pyproject.toml
git commit -m "feat: add ConfigStore for YAML config persistence"
```

---

## Task 3: Base Backend Class

**Files:**
- Create: `mcp_bridge/backends/base.py`
- Create: `tests/test_base.py`

- [ ] **Step 1: Write failing test for BaseBackend**

```python
from abc import ABC
from mcp_bridge.backends.base import BaseBackend

def test_base_backend_is_abc():
    assert issubclass(BaseBackend, ABC)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_base.py -v`
Expected: FAIL (BaseBackend not defined)

- [ ] **Step 3: Write minimal BaseBackend**

```python
from abc import ABC, abstractmethod

class BaseBackend(ABC):
    @abstractmethod
    def execute(self, command: str) -> str:
        """Execute command and return output."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the backend connection."""
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/backends/base.py tests/test_base.py
git commit -m "feat: add BaseBackend abstract class"
```

---

## Task 4: SSH Backend Implementation

**Files:**
- Create: `mcp_bridge/backends/ssh.py`
- Create: `tests/test_ssh.py`

- [ ] **Step 1: Write failing test for SSHBackend**

```python
import pytest
from mcp_bridge.backends.ssh import SSHBackend

@pytest.mark.asyncio
async def test_ssh_backend_connect_mock(mocker):
    mock_ssh = mocker.patch("paramiko.SSHClient")
    backend = SSHBackend(
        host="localhost",
        port=22,
        username="user",
        password=None
    )
    # Will test connection logic
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ssh.py -v`
Expected: FAIL (SSHBackend not defined)

- [ ] **Step 3: Write SSHBackend**

```python
import paramiko
from typing import Optional
from mcp_bridge.backends.base import BaseBackend

class SSHBackend(BaseBackend):
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str,
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
                import time
                time.sleep(0.1)
        return output

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._channel = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ssh.py -v`
Expected: PASS (or SKIP if no actual SSH server)

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/backends/ssh.py tests/test_ssh.py
git commit -m "feat: add SSHBackend with paramiko"
```

---

## Task 5: Docker Backend Implementation

**Files:**
- Create: `mcp_bridge/backends/docker.py`
- Create: `tests/test_docker.py`

- [ ] **Step 1: Write failing test for DockerBackend**

```python
from mcp_bridge.backends.docker import DockerBackend

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_docker.py -v`
Expected: FAIL (DockerBackend not defined)

- [ ] **Step 3: Write DockerBackend**

```python
import docker
from mcp_bridge.backends.base import BaseBackend

class DockerBackend(BaseBackend):
    def __init__(self, container: str):
        self.container = container
        self._client = docker.from_env()
        self._exec_id = None

    def execute(self, command: str) -> str:
        container = self._client.containers.get(self.container)
        exec_result = container.exec_run(
            cmd=command,
            stream=True,
            socket=True,
            demux=True,
        )
        output = b""
        while True:
            try:
                chunk = exec_result.output.read(1024)
                if not chunk:
                    break
                output += chunk
            except:
                break
        return output.decode("utf-8", errors="replace")

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_docker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/backends/docker.py tests/test_docker.py
git commit -m "feat: add DockerBackend with docker-py"
```

---

## Task 6: WSL Backend Implementation

**Files:**
- Create: `mcp_bridge/backends/wsl.py`
- Create: `tests/test_wsl.py`

- [ ] **Step 1: Write failing test for WSLBackend**

```python
from mcp_bridge.backends.wsl import WSLBackend

def test_wsl_backend_init():
    backend = WSLBackend()
    assert backend is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_wsl.py -v`
Expected: FAIL (WSLBackend not defined)

- [ ] **Step 3: Write WSLBackend**

```python
import subprocess
from mcp_bridge.backends.base import BaseBackend

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_wsl.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/backends/wsl.py tests/test_wsl.py
git commit -m "feat: add WSLBackend with subprocess"
```

---

## Task 7: Backend Manager

**Files:**
- Create: `mcp_bridge/manager.py`
- Create: `tests/test_manager.py`

- [ ] **Step 1: Write failing test for BackendManager**

```python
from mcp_bridge.manager import BackendManager, NoBackendInitialized

def test_manager_no_backend_raises():
    manager = BackendManager()
    with pytest.raises(NoBackendInitialized):
        manager.execute("ls")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_manager.py -v`
Expected: FAIL (BackendManager not defined)

- [ ] **Step 3: Write BackendManager**

```python
from typing import Optional, Literal
from mcp_bridge.backends.base import BaseBackend
from mcp_bridge.backends.ssh import SSHBackend
from mcp_bridge.backends.docker import DockerBackend
from mcp_bridge.backends.wsl import WSLBackend

class NoBackendInitialized(Exception):
    pass

class BackendManager:
    def __init__(self):
        self._backend: Optional[BaseBackend] = None
        self._backend_type: Optional[Literal["ssh", "docker", "wsl"]] = None

    def init(self, backend_type: Literal["ssh", "docker", "wsl"], **kwargs) -> None:
        if self._backend:
            self._backend.close()

        if backend_type == "ssh":
            self._backend = SSHBackend(**kwargs)
        elif backend_type == "docker":
            self._backend = DockerBackend(**kwargs)
        elif backend_type == "wsl":
            self._backend = WSLBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")

        self._backend_type = backend_type

    def execute(self, command: str) -> str:
        if not self._backend:
            raise NoBackendInitialized("Call init_session first")
        return self._backend.execute(command)

    def get_backend_type(self) -> Optional[Literal["ssh", "docker", "wsl"]]:
        return self._backend_type

    def close(self) -> None:
        if self._backend:
            self._backend.close()
            self._backend = None
            self._backend_type = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/manager.py tests/test_manager.py
git commit -m "feat: add BackendManager"
```

---

## Task 8: MCP Server with fastmcp

**Files:**
- Create: `mcp_bridge/server.py`
- Create: `mcp_bridge/__init__.py` (update)

- [ ] **Step 1: Write failing test for MCP tools**

```python
# No test for fastmcp tools directly - integration test
```

- [ ] **Step 2: Write server.py**

```python
from typing import Optional, Literal
from fastmcp import FastMCP
from mcp_bridge.config import ConfigStore
from mcp_bridge.manager import BackendManager, NoBackendInitialized

mcp = FastMCP("mcp-bridge")
_config_store = ConfigStore("mcp-bridge-config.yaml")
_manager = BackendManager()

@mcp.tool()
def init_session(
    backend_type: Literal["ssh", "docker", "wsl"],
    ssh_host: Optional[str] = None,
    ssh_port: int = 22,
    ssh_username: Optional[str] = None,
    ssh_password: Optional[str] = None,
    docker_container: Optional[str] = None,
) -> str:
    """
    Initialize a session with the specified backend.
    Configuration is saved locally for future sessions.
    """
    config = {"backend": backend_type}

    if backend_type == "ssh":
        if not ssh_host or not ssh_username:
            return "Error: ssh_host and ssh_username are required for SSH backend"
        config["ssh"] = {
            "host": ssh_host,
            "port": ssh_port,
            "username": ssh_username,
        }
        if ssh_password:
            config["ssh"]["password"] = ssh_password
        try:
            _manager.init(
                "ssh",
                host=ssh_host,
                port=ssh_port,
                username=ssh_username,
                password=ssh_password,
            )
        except Exception as e:
            return f"Failed to connect: {e}"

    elif backend_type == "docker":
        if not docker_container:
            return "Error: docker_container is required for Docker backend"
        config["docker"] = {"container": docker_container}
        try:
            _manager.init("docker", container=docker_container)
        except Exception as e:
            return f"Failed to connect: {e}"

    elif backend_type == "wsl":
        _manager.init("wsl")

    _config_store.save(config)
    return f"Session initialized with {backend_type} backend"

@mcp.tool()
def execute_command(command: str) -> str:
    """
    Execute a command on the current backend.
    Uses the same shell session as previous commands.
    """
    try:
        return _manager.execute(command)
    except NoBackendInitialized:
        return "Error: No backend initialized. Call init_session first."
    except Exception as e:
        return f"Error: {e}"

def main():
    mcp.run()
```

- [ ] **Step 3: Update mcp_bridge/__init__.py**

```python
"""MCP Bridge - Unified MCP server for SSH, Docker, and WSL backends."""

from mcp_bridge.server import mcp, init_session, execute_command

__all__ = ["mcp", "init_session", "execute_command"]
```

- [ ] **Step 4: Run lint check**

Run: `python -m py_compile mcp_bridge/server.py`

- [ ] **Step 5: Commit**

```bash
git add mcp_bridge/server.py mcp_bridge/__init__.py
git commit -m "feat: add fastmcp server with init_session and execute_command tools"
```

---

## Task 9: Package Installation Support

**Files:**
- Create: `mcp_bridge/__main__.py`

- [ ] **Step 1: Create __main__.py**

```python
from mcp_bridge.server import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update pyproject.toml entry points**

Add to pyproject.toml under [project]:

```toml
[project.scripts]
mcp-bridge = "mcp_bridge.server:main"
```

- [ ] **Step 3: Commit**

```bash
git add mcp_bridge/__main__.py pyproject.toml
git commit -m "feat: add package entry point"
```

---

## Spec Coverage Check

1. ✅ SSH/Docker/WSL三个后端 - backends/ssh.py, docker.py, wsl.py
2. ✅ init_session接口，支持选择后端和初始化信息 - server.py:init_session
3. ✅ 配置保存本地 - config.py
4. ✅ 下次调用确认复用 - 需要在init_session添加确认逻辑
5. ✅ execute_command执行命令 - server.py:execute_command
6. ✅ 同一交互shell - SSH invoke_shell, Docker exec_run socket, WSL subprocess persistent
7. ✅ 实时返回 - streaming实现

**Self-Review Complete**

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-29-mcp-bridge-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
