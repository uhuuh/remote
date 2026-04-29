# Remote MCP 配置重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 移除配置保存，改为每次连接都需要传参；统一错误分类

**Architecture:** 移除 ConfigStore，修改 BackendManager 增加自定义异常类，修改 __init__.py 简化初始化逻辑

**Tech Stack:** Python, FastMCP, paramiko, docker-py

---

## 文件变更概览

| 文件 | 操作 |
|------|------|
| `remote_mcp/__init__.py` | 修改 - 移除 ConfigStore，简化 init_session |
| `remote_mcp/manager.py` | 修改 - 增加自定义异常类 |
| `remote_mcp/config.py` | 删除 |

---

### Task 1: 修改 manager.py - 添加自定义异常类

**Files:**
- Modify: `remote_mcp/manager.py:1-42`

- [ ] **Step 1: 编写失败的测试**

```python
# tests/test_manager.py
import pytest
from remote_mcp.manager import BackendManager, NoSessionError, ConnectionError, ConfigError

def test_no_session_error():
    manager = BackendManager()
    with pytest.raises(NoSessionError):
        manager.execute("echo hello")
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_manager.py::test_no_session_error -v`
Expected: FAIL - name 'NoSessionError' not defined

- [ ] **Step 3: 实现异常类**

在 `remote_mcp/manager.py` 顶部添加：

```python
class NoSessionError(Exception):
    pass

class ConnectionError(Exception):
    pass

class ConfigError(Exception):
    pass
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_manager.py::test_no_session_error -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add remote_mcp/manager.py tests/test_manager.py
git commit -m "feat: add custom exception classes"
```

---

### Task 2: 修改 __init__.py - 移除 ConfigStore

**Files:**
- Modify: `remote_mcp/__init__.py:1-96`
- Delete: `remote_mcp/config.py`

- [ ] **Step 1: 编写失败的测试**

```python
# tests/test_init.py
def test_init_session_no_config_save():
    # 验证 init_session 不再保存配置到文件
    pass

def test_connection_error_format():
    # 验证连接失败返回格式
    pass

def test_config_error_format():
    # 验证配置错误返回格式
    pass

def test_no_session_error_message():
    # 验证未初始化错误信息
    pass
```

- [ ] **Step 2: 修改 __init__.py**

```python
# remote_mcp/__init__.py
from typing import Optional, Literal
from fastmcp import FastMCP
from remote_mcp.manager import BackendManager, NoSessionError, ConnectionError, ConfigError

mcp = FastMCP("mcp-bridge")
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
    Initialize a session with the specified backend type.

    Establishes a persistent connection to SSH, Docker, or WSL backend.

    Args:
        backend_type: Type of backend - "ssh", "docker", or "wsl"
        ssh_host: SSH server hostname (required for ssh)
        ssh_port: SSH server port (default: 22)
        ssh_username: SSH username (required for ssh)
        ssh_password: SSH password (optional, key auth attempted first)
        docker_container: Docker container name or ID (required for docker)

    Returns:
        Success message or error description
    """
    if backend_type == "ssh":
        if not ssh_host or not ssh_username:
            return f"配置错误: ssh_host 和 ssh_username 为必填项"
        try:
            _manager.init(
                "ssh",
                host=ssh_host,
                port=ssh_port,
                username=ssh_username,
                password=ssh_password,
            )
        except Exception as e:
            return f"连接失败: {e}"

    elif backend_type == "docker":
        if not docker_container:
            return f"配置错误: docker_container 为必填项"
        try:
            _manager.init("docker", container=docker_container)
        except Exception as e:
            return f"连接失败: {e}"

    elif backend_type == "wsl":
        _manager.init("wsl")

    return f"Session initialized with {backend_type} backend"

@mcp.tool()
def execute_command(command: str) -> str:
    """
    Execute a shell command on the active backend.

    Executes the command within a persistent shell session, preserving state
    across multiple commands (current directory, environment variables, etc.).

    Args:
        command: Shell command to execute

    Returns:
        Command output (stdout/stderr) or error message
    """
    try:
        return _manager.execute(command)
    except NoSessionError:
        return "错误: 请先调用 init_session 初始化会话"
    except Exception as e:
        return f"内部错误: {e}"
```

- [ ] **Step 3: 删除 config.py**

```bash
rm remote_mcp/config.py
```

- [ ] **Step 4: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add remote_mcp/__init__.py
git rm remote_mcp/config.py
git commit -m "refactor: remove config save, add unified error handling"
```

---

**Plan complete.** Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task
2. **Inline Execution** - Execute tasks in this session

Which approach?