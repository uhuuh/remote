from typing import Optional, Literal
from fastmcp import FastMCP
from mcp_bridge.config import ConfigStore
from mcp_bridge.manager import BackendManager, NoBackendInitialized

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
    Initialize a session with the specified backend.
    Configuration is saved locally for future sessions.
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
    Execute a command on the current backend.
    Uses the same shell session as previous commands.
    """
    try:
        return _manager.execute(command)
    except NoBackendInitialized:
        return "Error: No backend initialized. Call init_session first."
    except Exception as e:
        return f"Error: {e}"

def main():
    mcp.run()
