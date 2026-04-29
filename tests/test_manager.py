import pytest
from remote_mcp.manager import BackendManager, NoBackendInitialized

def test_manager_no_backend_raises():
    manager = BackendManager()
    with pytest.raises(NoBackendInitialized):
        manager.execute("ls")

def test_manager_init_ssh():
    manager = BackendManager()
    manager.init("ssh", host="localhost", username="user", port=22)
    assert manager.get_backend_type() == "ssh"

def test_manager_init_docker():
    manager = BackendManager()
    manager.init("docker", container="nginx")
    assert manager.get_backend_type() == "docker"

def test_manager_init_wsl():
    manager = BackendManager()
    manager.init("wsl")
    assert manager.get_backend_type() == "wsl"
