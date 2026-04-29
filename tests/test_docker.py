import pytest
import subprocess
import itertools
from remote_mcp.backends.docker import DockerBackend
from unittest.mock import patch, MagicMock

def test_docker_backend_init():
    backend = DockerBackend(container="nginx")
    assert backend.container == "nginx"

@patch('subprocess.Popen')
def test_docker_execute_command(MockPopen):
    mock_process = MagicMock()
    mock_process.stdout.read.side_effect = itertools.chain([b"file1\nfile2\n"], itertools.repeat(b""))
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
    mock_process.stdout.read.side_effect = itertools.repeat(b"")
    mock_process.wait.return_value = 1
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    result = backend.execute("badcommand")

    assert result == ""

@patch('subprocess.Popen')
def test_docker_shell_environment(MockPopen):
    mock_process = MagicMock()
    mock_process.stdout.read.side_effect = itertools.repeat(b"")
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
    mock_process.stdout.read.side_effect = itertools.repeat(b"")
    mock_process.wait.return_value = 0
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")

    backend.execute("cd /tmp")
    backend.execute("pwd")

    assert MockPopen.call_count == 2

@patch('subprocess.Popen')
def test_docker_streaming_returns_partial_output(MockPopen):
    """验证流式返回：第一次 read 返回部分数据时就立即返回给调用方"""
    mock_process = MagicMock()
    first_chunk = [b"partial"]
    mock_process.stdout.read.side_effect = lambda size: first_chunk.pop(0) if first_chunk else b""
    mock_process.wait.return_value = 0
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    result = backend.execute("long_running_command")

    # 验证能获取到第一次返回的部分数据
    assert "partial" in result

@patch('subprocess.Popen')
def test_docker_multiple_read_cycles(MockPopen):
    """验证循环读取 - 每次 read 被调用都应检查是否有新数据"""
    mock_process = MagicMock()
    read_calls = []
    def track_read(size):
        read_calls.append(size)
        if len(read_calls) == 1:
            return b"first"
        elif len(read_calls) == 2:
            return b"second"
        else:
            return b""

    mock_process.stdout.read.side_effect = track_read
    mock_process.wait.return_value = 0
    MockPopen.return_value = mock_process

    backend = DockerBackend(container="nginx")
    result = backend.execute("test")

    # 验证 read 被调用了多次
    assert len(read_calls) >= 2
    # 验证每次调用都传入了正确的缓冲区大小
    for size in read_calls[:-1]:
        assert size == 1024