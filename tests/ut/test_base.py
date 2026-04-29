from abc import ABC
from remote_mcp.backends.base import BaseBackend

def test_base_backend_is_abc():
    assert issubclass(BaseBackend, ABC)
