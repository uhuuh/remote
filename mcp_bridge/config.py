import yaml
from pathlib import Path
from typing import Optional

class ConfigStore:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)

    def save(self, config: dict) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(config, f)

    def load(self) -> Optional[dict]:
        if not self.config_path.exists():
            return None
        with open(self.config_path) as f:
            return yaml.safe_load(f)
