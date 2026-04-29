from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


@dataclass
class ConnectionConfig:
    type: Literal["ssh", "docker", "wsl"]
    host: Optional[str] = None
    port: int = 22
    username: Optional[str] = None
    password: Optional[str] = None
    container: Optional[str] = None


@dataclass
class SyncConfig:
    enabled: bool = False
    remote_path: str = ""


@dataclass
class ExecuteConfig:
    tasks: Dict[str, str] = field(default_factory=dict)
    pipeline: List[str] = field(default_factory=list)


@dataclass
class Config:
    connection: ConnectionConfig
    sync: SyncConfig = field(default_factory=SyncConfig)
    execute: ExecuteConfig = field(default_factory=ExecuteConfig)
