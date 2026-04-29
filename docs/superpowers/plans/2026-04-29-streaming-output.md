# 流式输出实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 三个后端（SSH/Docker/WSL）的 execute 方法改为实时流式返回命令执行过程中的输出

**Architecture:** SSH 使用 exec_command + 循环读取 stdout；Docker/WSL 使用 Popen + 循环读取 stdout

**Tech Stack:** Python, paramiko, subprocess

---

## 文件变更

| 文件 | 操作 |
|------|------|
| `remote_mcp/backends/ssh.py` | 修改 - exec_command + 流式读取 |
| `remote_mcp/backends/docker.py` | 修改 - Popen + 流式读取 |
| `remote_mcp/backends/wsl.py` | 修改 - Popen + 流式读取 |

---

### Task 1: SSHBackend 流式输出

**Files:**
- Modify: `remote_mcp/backends/ssh.py:45-60`

- [ ] **Step 1: 修改 SSHBackend**

```python
def execute(self, command: str) -> str:
    self._connect()

    stdin, stdout, stderr = self._client.exec_command(
        f"/bin/bash -l -c '{command.replace('\'', '\'\"\'\'')}'"
    )

    output = ""
    while True:
        chunk = stdout.read(1024)
        if not chunk:
            break
        output += chunk.decode("utf-8")

    error = stderr.read().decode("utf-8")
    return output + error
```

- [ ] **Step 2: 测试验证**

Run: `pytest tests/test_ssh.py tests/test_manager.py -v`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add remote_mcp/backends/ssh.py
git commit -m "refactor: SSHBackend streaming output"
```

---

### Task 2: DockerBackend 流式输出

**Files:**
- Modify: `remote_mcp/backends/docker.py:8-17`

- [ ] **Step 1: 修改 DockerBackend**

```python
def execute(self, command: str) -> str:
    process = subprocess.Popen(
        ["docker", "exec", "-i", self.container, "/bin/bash", "-l", "-c", command],
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
```

- [ ] **Step 2: 测试验证**

Run: `pytest tests/test_docker.py -v`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add remote_mcp/backends/docker.py
git commit -m "refactor: DockerBackend streaming output"
```

---

### Task 3: WSLBackend 流式输出

**Files:**
- Modify: `remote_mcp/backends/wsl.py:23-30`

- [ ] **Step 1: 修改 WSLBackend**

```python
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
```

- [ ] **Step 2: 测试验证**

Run: `pytest tests/test_wsl.py -v`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add remote_mcp/backends/wsl.py
git commit -m "refactor: WSLBackend streaming output"
```

---

**Plan complete.** 选择执行方式：
1. Subagent-Driven (recommended)
2. Inline Execution