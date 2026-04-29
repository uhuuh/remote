import pytest
import os

class TestSSHRealBackend:
    """SSH 后端真实环境测试 - 需要 SSH 环境变量配置"""

    @pytest.fixture
    def ssh_config(self):
        return {
            "host": os.environ.get("TEST_SSH_HOST", "localhost"),
            "port": int(os.environ.get("TEST_SSH_PORT", 22)),
            "username": os.environ.get("TEST_SSH_USER", "root"),
            "password": os.environ.get("TEST_SSH_PASSWORD"),
        }

    def test_ssh_connect(self, ssh_config):
        from remote_mcp.backends.ssh import SSHBackend

        backend = SSHBackend(
            host=ssh_config["host"],
            port=ssh_config["port"],
            username=ssh_config["username"],
            password=ssh_config.get("password"),
        )

        result = backend.execute("echo hello")
        assert "hello" in result.lower()

    def test_ssh_environment(self, ssh_config):
        from remote_mcp.backends.ssh import SSHBackend

        backend = SSHBackend(
            host=ssh_config["host"],
            port=ssh_config["port"],
            username=ssh_config["username"],
            password=ssh_config.get("password"),
        )

        result = backend.execute("echo $HOME")
        assert result.strip()

    def test_ssh_long_output(self, ssh_config):
        from remote_mcp.backends.ssh import SSHBackend

        backend = SSHBackend(
            host=ssh_config["host"],
            port=ssh_config["port"],
            username=ssh_config["username"],
            password=ssh_config.get("password"),
        )

        result = backend.execute("seq 1 100 | head -20")
        lines = result.strip().split("\n")
        assert len(lines) > 5


class TestDockerRealBackend:
    """Docker 后端真实环境测试 - 需要 Docker 环境"""

    def test_docker_execute(self):
        from remote_mcp.backends.docker import DockerBackend

        backend = DockerBackend(container="nginx")

        result = backend.execute("echo hello")
        assert "hello" in result.lower()

    def test_docker_environment(self):
        from remote_mcp.backends.docker import DockerBackend

        backend = DockerBackend(container="nginx")

        result = backend.execute("echo $HOME")
        assert result.strip()

    def test_docker_long_output(self):
        from remote_mcp.backends.docker import DockerBackend

        backend = DockerBackend(container="nginx")

        result = backend.execute("seq 1 100 | head -20")
        lines = result.strip().split("\n")
        assert len(lines) > 5

    def test_docker_stderr(self):
        from remote_mcp.backends.docker import DockerBackend

        backend = DockerBackend(container="nginx")

        result = backend.execute("ls /nonexistent 2>&1")
        assert "no such file" in result.lower() or "cannot access" in result.lower()


class TestWSLRealBackend:
    """WSL 后端真实环境测试 - 需要 WSL 环境"""

    def test_wsl_execute(self):
        from remote_mcp.backends.wsl import WSLBackend

        backend = WSLBackend()

        result = backend.execute("echo hello")
        assert "hello" in result.lower()

    def test_wsl_environment(self):
        from remote_mcp.backends.wsl import WSLBackend

        backend = WSLBackend()

        result = backend.execute("echo $HOME")
        assert result.strip()

    def test_wsl_long_output(self):
        from remote_mcp.backends.wsl import WSLBackend

        backend = WSLBackend()

        result = backend.execute("seq 1 100 | head -20")
        lines = result.strip().split("\n")
        assert len(lines) > 5


class TestManagerIntegration:
    """Manager 集成测试"""

    def test_manager_no_session_error(self):
        from remote_mcp.manager import BackendManager, NoSessionError

        manager = BackendManager()
        with pytest.raises(NoSessionError):
            manager.execute("echo hello")

    def test_manager_config_error(self):
        from remote_mcp.manager import BackendManager, ConfigError

        manager = BackendManager()
        with pytest.raises(ConfigError):
            manager.init("unknown_type")