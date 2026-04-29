# Remote Runner Design

## Overview

单文件 Python 工具，用于连接远程后端、同步代码、执行任务。

## File Structure

- 单文件 `remote_runner.py`
- 入口函数 `main()`

## Config Structure

```python
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

@dataclass
class ConnectionConfig:
    backend: Literal["ssh", "docker", "wsl"]
    ssh_host: Optional[str] = None
    ssh_port: int = 22
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    docker_container: Optional[str] = None

@dataclass
class SyncConfig:
    enabled: bool = False
    remote_path: str = ""

@dataclass
class ExecuteConfig:
    tasks: Dict[str, str]    # name -> command
    pipeline: List[str]      # 执行顺序（tasks 中的 key）

@dataclass
class Config:
    connection: ConnectionConfig
    sync: SyncConfig
    execute: ExecuteConfig
```

## Workflow

### 1. 初始化连接
根据 `connection` 配置创建对应 Backend（SSH/Docker/WSL）。

### 2. 同步代码（可选）
- 仅当 `sync.enabled == True` 时执行
- **Patch 生成**：本地执行 `git diff HEAD`，排除当前文件（`remote_runner.py`）
- **Commit 创建**：本地创建提交
- **Patch 应用**：通过 backend 上传 patch 内容，远程执行 `git apply`
- **远程 Commit**：远程同样创建相应提交
- **失败处理**：抛出 `SyncError` 异常，包含 stderr 详情
- **严格模式**：任何 hunk 失败 → 抛出异常

### 3. 执行任务
- 按 `pipeline` 顺序执行 `execute.tasks` 中的任务
- 实时输出：使用 `subprocess.Popen` + `iter_stdout/stderr`，输出即时打印
- **失败处理**：任务失败立即中断，抛出异常

## Error Handling

| 阶段 | 异常类型 | 处理方式 |
|------|----------|----------|
| 连接 | `ConnectionError` | 抛出 |
| 同步 | `SyncError` | 抛出，包含 stderr |
| 执行 | `ExecuteError` | 抛出，中断 pipeline |

## Dependencies

- paramiko（SSH）
- docker（Docker）
- 标准库：subprocess, dataclasses, typing
