import pytest
from remote_mcp.backends.docker import DockerBackend
from unittest.mock import patch, MagicMock

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"

@patch('subprocess.run')
def test_docker_execute_command(MockRun):
    mock_result = MagicMock()
    mock_result.stdout = "file1\nfile2\n"
    mock_result.stderr = ""
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")
    result = backend.execute("ls")

    MockRun.assert_called_once_with(
        ["docker", "exec", "nginx", "/bin/bash", "-l", "-c", "ls"],
        capture_output=True,
        text=True,
    )
    assert "file1" in result

@patch('subprocess.run')
def test_docker_execute_error(MockRun):
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.stderr = "command not found"
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")
    result = backend.execute("badcommand")

    assert "command not found" in result

@patch('subprocess.run')
def test_docker_shell_environment(MockRun):
    mock_result = MagicMock()
    mock_result.stdout = "/root\n"
    mock_result.stderr = ""
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")
    backend.execute("echo $HOME")

    call_args = MockRun.call_args[0][0]
    assert "/bin/bash" in call_args
    assert "-l" in call_args

@patch('subprocess.run')
def test_docker_no_persistence(MockRun):
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.stderr = ""
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")

    backend.execute("cd /tmp")
    backend.execute("pwd")

    assert MockRun.call_count == 2