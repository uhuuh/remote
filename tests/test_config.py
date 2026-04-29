import os
import tempfile
from mcp_bridge.config import ConfigStore

def test_config_store_save_and_load():
    store = ConfigStore("test_config.yaml")
    config = {
        "backend": "ssh",
        "ssh": {"host": "192.168.1.1", "port": 22, "username": "user"},
    }
    store.save(config)
    loaded = store.load()
    assert loaded == config
    os.remove("test_config.yaml")

def test_config_store_load_returns_none_for_missing_file():
    store = ConfigStore("nonexistent.yaml")
    assert store.load() is None
