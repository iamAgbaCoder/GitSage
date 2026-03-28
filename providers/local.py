import requests
from .base import AIProvider


class LocalProvider(AIProvider):
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"

    def generate(self, prompt: str) -> str:
        try:
            payload = {"model": self.model_name, "prompt": prompt, "stream": False}
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.RequestException as e:
            raise RuntimeError(
                f"Local Engine API error. Is your local proxy/service running? Error: {str(e)}"
            )

    async def generate_async(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(self.generate, prompt)
