# MCP Bridge Server Design

## Overview

An MCP server that provides unified interface to SSH, Docker, and WSL backends through fastmcp.

## Architecture

```
MCP Clients → MCP Server (fastmcp) → BackendManager → SSH/Docker/WSL
```

### Components

- **BackendManager** - Manages backend lifecycle and configuration
- **SSHBackend** - SSH connection via paramiko (password or key)
- **DockerBackend** - Docker connection via docker-py (Unix Socket)
- **WSLBackend** - Local WSL execution via subprocess
- **ConfigStore** - YAML-based persistent configuration

## Interfaces

### 1. init_session

First call: prompts user to select backend type and enter configuration.
- Saves config to `./mcp-bridge-config.yaml`
- Establishes persistent connection

Subsequent calls: reads saved config, confirms whether to reuse.

**Parameters:**
- `backend_type`: "ssh" | "docker" | "wsl"
- `ssh_host`: str (SSH only)
- `ssh_port`: int (SSH only, default 22)
- `ssh_username`: str (SSH only)
- `ssh_password`: str (SSH only, optional, 如果提供则优先尝试key，失败后用password)
- `docker_container`: str (Docker only, container name or ID)

Note: SSH尝试key认证，失败则回退到密码认证。Docker支持容器名或ID。

**Response:**
- Success/failure status
- Backend type confirmed

### 2. execute_command

Executes command on the active backend within the same interactive shell session.

**Parameters:**
- `command`: str - Command to execute

**Response:**
- Real-time stdout/stderr streaming
- Exit code

## Data Storage

Config file: `./mcp-bridge-config.yaml` (current project directory)

```yaml
backend: ssh | docker | wsl
ssh:
  host: str
  port: int
  username: str
  password: str  # optional, encrypted or plaintext
docker:
  container: str
wsl: {}
```

## Session Persistence

- SSH: maintains paramiko transport channel across commands
- Docker: reuses same docker client instance
- WSL: reuses same subprocess across commands

## Error Handling

- Connection failures → clear error message + retry option
- Backend not initialized → prompt to call init_session first
