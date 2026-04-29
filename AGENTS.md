# Remote MCP

MCP server providing unified SSH/Docker/WSL command execution via fastmcp.

## Run

```bash
python -m remote_mcp
# or after pip install:
mcp-bridge
```

## Test

```bash
pytest
```

## Architecture

- `remote_mcp/__init__.py` - FastMCP server entrypoint; exposes `init_session` and `execute_command` tools
- `remote_mcp/manager.py` - BackendManager routes to SSH/Docker/WSL backends
- `remote_mcp/backends/{ssh,docker,wsl}.py` - Backend implementations
- `remote_mcp/config.py` - ConfigStore saves/loads `mcp-bridge-config.yaml`

## Key Patterns

- SSHBackend uses paramiko with key-first auth, fallback to password
- DockerBackend uses docker-py Unix socket
- WSLBackend reuses a single subprocess.Popen shell across commands
- All backends share persistent session (channel/transport) across `execute_command` calls

## Dependencies

- fastmcp, paramiko, docker, pyyaml
- dev: pytest, pytest-asyncio
