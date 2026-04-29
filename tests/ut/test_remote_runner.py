import pytest
from unittest.mock import Mock, patch
from remote_runner import (
    ConnectionConfig,
    SyncConfig,
    ExecuteConfig,
    Config,
    BackendManager,
    CommandResult,
    SyncManager,
    SyncError,
    ExecuteError,
    TaskExecutor,
)


class TestConnectionConfig:
    def test_ssh_config(self):
        config = ConnectionConfig(
            type="ssh",
            host="localhost",
            username="user",
            password="pass",
        )
        assert config.type == "ssh"
        assert config.host == "localhost"
        assert config.username == "user"
        assert config.password == "pass"

    def test_docker_config(self):
        config = ConnectionConfig(
            type="docker",
            container="my-container",
        )
        assert config.type == "docker"
        assert config.container == "my-container"

    def test_wsl_config(self):
        config = ConnectionConfig(type="wsl")
        assert config.type == "wsl"


class TestConfig:
    def test_full_config(self):
        config = Config(
            connection=ConnectionConfig(type="ssh", host="localhost", username="user", remote_path="/remote/path"),
            sync=SyncConfig(enabled=True),
            execute=ExecuteConfig(
                tasks={"build": "npm run build", "test": "npm test"},
                pipeline=["test", "build"],
            ),
        )
        assert config.connection.type == "ssh"
        assert config.connection.remote_path == "/remote/path"
        assert config.sync.enabled is True
        assert config.execute.pipeline == ["test", "build"]


class TestBackendManager:
    def test_execute_with_result_parses_exit_code(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        manager = BackendManager(config)

        with patch.object(manager, 'execute') as mock_execute:
            mock_execute.return_value = "output\nEXIT_CODE=0"
            result = manager.execute_with_result("echo test")

        assert result.returncode == 0
        assert result.stdout == "output"

    def test_execute_with_result_handles_nonzero_exit(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        manager = BackendManager(config)

        with patch.object(manager, 'execute') as mock_execute:
            mock_execute.return_value = "error\nEXIT_CODE=1"
            result = manager.execute_with_result("echo test")

        assert result.returncode == 1


class TestSyncManager:
    def test_sync_disabled_does_nothing(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        manager = BackendManager(config)
        sync_config = SyncConfig(enabled=False)
        sync_mgr = SyncManager(manager, sync_config)

        sync_mgr.sync("/some/file.py")

    def test_generate_patch_excludes_current_file(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user", remote_path="/tmp")
        manager = BackendManager(config)
        sync_config = SyncConfig(enabled=True)
        sync_mgr = SyncManager(manager, sync_config)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="diff content", returncode=0)
            patch_content = sync_mgr._generate_patch("/some/path/remote_runner.py")

        assert "remote_runner.py" not in patch_content


class TestTaskExecutor:
    def test_execute_pipeline_task_not_found(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        manager = BackendManager(config)
        exec_config = ExecuteConfig(
            tasks={"build": "echo build"},
            pipeline=["test"],
        )
        executor = TaskExecutor(manager, exec_config)

        with pytest.raises(ExecuteError, match="Task 'test' not found"):
            executor.execute_pipeline()

    def test_execute_pipeline_empty(self):
        config = ConnectionConfig(type="ssh", host="localhost", username="user")
        manager = BackendManager(config)
        exec_config = ExecuteConfig(tasks={}, pipeline=[])
        executor = TaskExecutor(manager, exec_config)

        executor.execute_pipeline()
