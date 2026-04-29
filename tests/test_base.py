from abc import ABC
from mcp_bridge.backends.base import BaseBackend

def test_base_backend_is_abc():
    assert issubclass(BaseBackend, ABC)
