from remote_mcp.backends.wsl import WSLBackend

def test_wsl_backend_init():
    backend = WSLBackend()
    assert backend is not None
