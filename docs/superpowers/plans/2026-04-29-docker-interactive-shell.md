# Docker Interactive Shell 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 DockerBackend 改为使用 subprocess 调用 docker exec -it 建立交互式 shell

**Architecture:** 重写 DockerBackend，使用 subprocess.Popen 替代 docker-py exec_run，与 WSL 后端模式一致

**Tech Stack:** Python, subprocess, docker

---

## 文件变更

| 文件 | 操作 |
|------|------|
| `remote_mcp/backends/docker.py` | 重写 |

---

### Task 1: 重写 DockerBackend

**Files:**
- Modify: `remote_mcp/backends/docker.py:1-30`

- [ ] **Step 1: 编写失败的测试**

```python
# tests/test_docker.py
import pytest
from remote_mcp.backends.docker import DockerBackend
from unittest.mock import Mock, patch, MagicMock

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"
    assert backend._process is None

def test_docker_backend_no_docker_client():
    """验证不再使用 docker-py 的 _client"""
    backend = DockerBackend(container="nginx")
    assert not hasattr(backend, '_client')

@patch('subprocess.Popen')
def test_docker_execute_command(MockPopen):
    """测试执行命令并返回输出"""
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.stdout.readline.side_effect = [
        "user@container:~$ ",
    ]
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    result = backend.execute("ls")

    MockPopen.assert_called_once_with(
        ["docker", "exec", "-it", "nginx", "/bin/bash"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    mock_process.stdin.write.assert_called_with("ls\n")
    assert "user@container:~$" in result

@patch('subprocess.Popen')
def test_docker_persistent_shell(MockPopen):
    """测试多次执行命令在同一个 shell 中"""
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.stdout.readline.side_effect = [
        "user@container:~$ ",
        "user@container:~$ ",
    ]
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")

    # 第一次执行
    backend.execute("cd /tmp")
    # 第二次执行
    backend.execute("ls")

    # 只应该创建一次进程
    assert MockPopen.call_count == 1
    assert mock_process.stdin.write.call_count == 2

@patch('subprocess.Popen')
def test_docker_shell_reconnect_on_crash(MockPopen):
    """测试 shell 崩溃后重新连接"""
    mock_process = MagicMock()
    mock_process.poll.return_value = 1  # 进程已退出
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")

    # 执行命令应该重新创建 shell
    backend.execute("ls")

    # 应该创建了新进程
    assert MockPopen.call_count == 1

@patch('subprocess.Popen')
def test_docker_close(MockPopen):
    """测试关闭后端"""
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    backend.execute("ls")
    backend.close()

    mock_process.terminate.assert_called_once()
    assert backend._process is None

@patch('subprocess.Popen')
def test_docker_prompt_detection(MockPopen):
    """测试检测不同类型的 prompt"""
    test_cases = [
        ("user@host:~$ ", True),
        ("root@container:/tmp# ", True),
        ("(prompt) ", False),
    ]

    for prompt, should_break in test_cases:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdout.readline.side_effect = [prompt]
        MockPopen.return_value = mock_process

        backend = DockerBackend(container="nginx")
        result = backend.execute("echo test")

        if should_break:
            assert prompt in result

@patch('subprocess.Popen')
def test_docker_environment_persistence(MockPopen):
    """测试环境变量持久化 - 多次执行在同一个 shell"""
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    outputs = [
        "export MYVAR=test",
        "user@container:~$ ",
        "echo $MYVAR",
        "test",
        "user@container:~$ ",
    ]
    mock_process.stdout.readline.side_effect = outputs
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")

    # 设置环境变量
    backend.execute("export MYVAR=test")
    # 读取环境变量
    result = backend.execute("echo $MYVAR")

    # 两次调用在同一个 shell 中
    assert MockPopen.call_count == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_docker.py::test_docker_backend_init -v`
Expected: PASS (测试只是检查 container 属性)

- [ ] **Step 3: 重写 DockerBackend**

```python
# remote_mcp/backends/docker.py
import subprocess
from remote_mcp.backends.base import BaseBackend

class DockerBackend(BaseBackend):
    def __init__(self, container: str):
        self.container = container
        self._process = None

    def _ensure_shell(self) -> None:
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(
                ["docker", "exec", "-it", self.container, "/bin/bash", "-l"],
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

- [ ] **Step 4: 运行测试验证**

Run: `pytest tests/test_docker.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add remote_mcp/backends/docker.py tests/test_docker.py
git commit -m "refactor: rewrite DockerBackend with subprocess exec"
```

---

**Plan complete.** Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task
2. **Inline Execution** - Execute tasks in this session

Which approach?