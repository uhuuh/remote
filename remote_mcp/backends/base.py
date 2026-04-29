from abc import ABC, abstractmethod

class BaseBackend(ABC):
    @abstractmethod
    def execute(self, command: str) -> str:
        """Execute command and return output."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the backend connection."""
        pass
