# 交互式终端命令结束检测问题

## 概述

在交互式 shell 会话中，无法直接通过连接库原生接口判断命令是否已执行完毕。

## 三个后端实现方式

| 后端 | 连接方式 | 命令发送 | 数据读取 |
|------|----------|----------|----------|
| **SSH** | paramiko `invoke_shell()` | `_channel.send()` | `_channel.recv()` |
| **Docker** | subprocess `Popen` | `stdin.write()` | `stdout.readline()` |
| **WSL** | subprocess `Popen` | `stdin.write()` | `stdout.readline()` |

## 核心问题

### 1. 无退出状态机制

`invoke_shell()` 创建的是交互式 shell，会话级别没有命令级别的退出状态。

```python
# SSH - paramiko 的限制
channel = client.invoke_shell()
channel.send("ls\n")
# 无法获取 "ls" 的退出状态
# 因为 shell 还在会话中，可能执行更多命令
```

### 2. recv_ready() 不能判断命令结束

```python
# SSH - paramiko
while True:
    if self._channel.recv_ready():
        data = self._channel.recv(1024)
        output += data
        if "$" in output or "#" in output:  # 问题在这里
            break
    else:
        time.sleep(0.1)  # 等待数据到达，但不意味命令结束
```

`recv_ready()` 返回 False 只表示：
- 当前缓冲区无数据
- 不代表命令已执行完
- 网络延迟可能导致数据还未到达

### 3. readline() 无法判断命令结束

```python
# Docker/WSL - subprocess
while True:
    line = self._process.stdout.readline()
    if not line:  # 空行不意味命令结束
        break
    output += line
    if "$" in line or "#" in line:  # 问题在这里
        break
```

`readline()` 返回空字符串可能因为：
- 数据还未到达
- 命令还在执行
- 真正的 EOF

## 当前解决方案及问题

### Prompt 检测 (`$` 或 `#`)

```python
if "$" in line or "#" in line:
    break
```

**问题：**
- 输出内容可能包含这些字符
- 非标准 prompt 会导致永远等待
- 某些命令执行后不显示 prompt

### 替代方案

| 方案 | 原理 | 适用场景 |
|------|------|----------|
| **echo 标记** | 追加 `echo "<<<END>>>"` | 持久会话，推荐 |
| **超时机制** | 固定时间后认为完成 | 不保证完整性 |
| **行数限制** | 读取固定行数 | 输出可预测的场景 |
| **PTY + EOF** | 关闭写端触发 EOF | 单次命令会话 |

### echo 标记法示例

```python
import uuid

def execute(self, command: str) -> str:
    marker = f"<<<{uuid.uuid4().hex[:8]}>>>"
    full_cmd = f"{command}; echo '{marker}'"

    self._channel.send(full_cmd + "\n")

    output = ""
    while True:
        if self._channel.recv_ready():
            data = self._channel.recv(1024).decode("utf-8")
            output += data
            if marker in output:
                output = output.replace(marker, "")
                break
        else:
            time.sleep(0.1)

    return output
```

## 结论

| 后端 | 原生接口判断结束 | 现实可行方案 |
|------|-------------------|--------------|
| SSH (paramiko) | ❌ 无法判断 | Prompt 检测 / echo 标记 |
| Docker (subprocess) | ❌ 无法判断 | Prompt 检测 / echo 标记 |
| WSL (subprocess) | ❌ 无法判断 | Prompt 检测 / echo 标记 |

所有交互式 shell 连接库都无法直接判断命令执行完毕，**prompt 检测是实际广泛使用的方案**，但存在误判风险。

如需更可靠的判断，建议使用 **echo 标记法**，但会修改输出内容。