from remote_mcp.backends.docker import DockerBackend

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"
