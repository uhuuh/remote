"""MCP Bridge - Unified MCP server for SSH, Docker, and WSL backends."""

from mcp_bridge.server import mcp, init_session, execute_command

__all__ = ["mcp", "init_session", "execute_command"]
