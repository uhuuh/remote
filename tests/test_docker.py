import pytest
import subprocess
from remote_mcp.backends.docker import DockerBackend
from unittest.mock import patch, MagicMock

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"

@patch('subprocess.Popen')
def test_docker_execute_command(MockPopen):
    mock_process = MagicMock()
    mock_process.stdout.read.side_effect = [b"file1\nfile2\n", b""]
    mock_process.wait.return_value = 0
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    result = backend.execute("ls")

    MockPopen.assert_called_once_with(
        ["docker", "exec", "-i", "nginx", "/bin/bash", "-l", "-c", "ls"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert "file1" in result

@patch('subprocess.Popen')
def test_docker_execute_error(MockPopen):
    mock_process = MagicMock()
    mock_process.stdout.read.side_effect = [b"", b""]
    mock_process.wait.return_value = 1
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    result = backend.execute("badcommand")

    assert result == ""

@patch('subprocess.Popen')
def test_docker_shell_environment(MockPopen):
    mock_process = MagicMock()
    mock_process.stdout.read.side_effect = [b"", b""]
    mock_process.wait.return_value = 0
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    backend.execute("echo $HOME")

    call_args = MockPopen.call_args[0][0]
    assert "/bin/bash" in call_args
    assert "-l" in call_args

@patch('subprocess.Popen')
def test_docker_no_persistence(MockPopen):
    mock_process = MagicMock()
    mock_process.stdout.read.side_effect = [b"", b""]
    mock_process.wait.return_value = 0
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")

    backend.execute("cd /tmp")
    backend.execute("pwd")

    assert MockPopen.call_count == 2