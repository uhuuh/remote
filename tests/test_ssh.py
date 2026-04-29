from mcp_bridge.backends.ssh import SSHBackend

def test_ssh_backend_init():
    backend = SSHBackend(
        host="localhost",
        username="user",
        port=22,
        password=None
    )
    assert backend.host == "localhost"
    assert backend.port == 22
    assert backend.username == "user"
    assert backend.password is None
