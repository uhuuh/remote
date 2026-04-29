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
            return "配置错误: ssh_host 和 ssh_username 为必填项"
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
            return "配置错误: docker_container 为必填项"
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

def main():
    mcp.run(transport="http", host="0.0.0.0", port=7000)