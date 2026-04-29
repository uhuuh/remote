import pytest
import subprocess
from remote_mcp.backends.docker import DockerBackend
from unittest.mock import patch

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"

@patch('subprocess.run')
def test_docker_execute_command(MockRun):
    """测试执行命令"""
    mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="file1\nfile2\n", stderr="")
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")
    result = backend.execute("ls")

    MockRun.assert_called_once_with(
        ["docker", "exec", "-i", "nginx", "/bin/bash", "-l", "-c", "ls"],
        capture_output=True,
        text=True,
    )
    assert result == "file1\nfile2\n"

@patch('subprocess.run')
def test_docker_execute_error(MockRun):
    """测试命令错误返回 stderr"""
    mock_result = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="command not found")
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")
    result = backend.execute("badcommand")

    assert "command not found" in result

@patch('subprocess.run')
def test_docker_shell_environment(MockRun):
    """测试使用 login shell (-l) 确保用户环境"""
    mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="echo $HOME", stderr="")
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")
    backend.execute("echo $HOME")

    call_args = MockRun.call_args[0][0]
    assert "/bin/bash" in call_args
    assert "-l" in call_args

@patch('subprocess.run')
def test_docker_no_persistence(MockRun):
    """测试每次执行是独立的（不持久化）"""
    mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    MockRun.return_value = mock_result

    backend = DockerBackend(container="nginx")

    backend.execute("cd /tmp")
    backend.execute("pwd")

    # 每次调用都是独立的 docker exec
    assert MockRun.call_count == 2