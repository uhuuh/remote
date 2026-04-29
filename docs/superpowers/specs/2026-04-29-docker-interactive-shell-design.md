# Docker Backend 交互式 Shell 设计

## 背景

当前 DockerBackend 使用 `docker-py` 的 `exec_run` 执行单条命令，无法提供交互式 shell体验。SSH 和 WSL 后端都使用持久化 shell，但 Docker 没有。

## 目标

让 Docker 后端也提供与普通用户一致的交互式 shell：
- 相同的环境变量（HOME, USER 等）
- 相同的命令执行体验（cd, source 等）
- 当前目录和环境变量跨命令持久化

## 实现方案

### DockerBackend 改为 subprocess 方式

使用 `subprocess.Popen` 调用 `docker exec -it` 建立持久化交互式 shell：

```python
import subprocess

class DockerBackend(BaseBackend):
    def __init__(self, container: str):
        self.container = container
        self._process = None

    def _ensure_shell(self) -> None:
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(
                ["docker", "exec", "-it", self.container, "/bin/bash"],
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

### 行为一致性

| 后端 | 持久化 | 交互方式 |
|------|--------|----------|
| SSH | 是 | paramiko invoke_shell |
| Docker | 是 | docker exec -it |
| WSL | 是 | subprocess.Popen wsl |

所有后端都通过 `_ensure_shell` 确保 shell 存在，通过 stdin/stdout 进行命令交互，通过检测 prompt（`$` 或 `#`）判断命令完成。

## 文件变更

- `remote_mcp/backends/docker.py` - 重写为 subprocess 方式