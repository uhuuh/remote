from typing import Optional, Literal
from fastmcp import FastMCP
from remote_mcp.config import ConfigStore
from remote_mcp.manager import BackendManager, NoBackendInitialized

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
    Initialize a session with the specified backend type.

    Establishes a persistent connection to SSH, Docker, or WSL backend.
    Configuration is saved to mcp-bridge-config.yaml for future sessions.

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
    except NoBackendInitialized:
        return "Error: No backend initialized. Call init_session first."
    except Exception as e:
        return f"Error: {e}"

def main():
    mcp.run()
