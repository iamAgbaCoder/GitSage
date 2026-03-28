from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from prompt. Should raise RuntimeError on failure."""
        pass

    @abstractmethod
    async def generate_async(self, prompt: str) -> str:
        """Generate text from prompt asynchronusly. Should raise RuntimeError on failure."""
        pass
