import os
from .base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.api_key = (
            api_key or os.getenv("GITSAGE_API_KEY") or os.getenv("GEMINI_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "GitSage API_KEY is missing. Please set it or add it to config."
            )

        try:
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except ImportError:
            raise ImportError(
                "google-generativeai package is not installed. Please install it."
            )

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            # handle case where text is potentially empty or blocked
            if getattr(response, "text", None):
                return response.text.strip()
            # fallback if 'parts' structure differs
            return response.parts[0].text.strip() if response.parts else ""
        except Exception as e:
            raise RuntimeError(f"Intelligence Engine communication error: {str(e)}")

    async def generate_async(self, prompt: str) -> str:
        try:
            response = await self.model.generate_content_async(prompt)
            # handle case where text is potentially empty or blocked
            if getattr(response, "text", None):
                return response.text.strip()
            # fallback if 'parts' structure differs
            return response.parts[0].text.strip() if response.parts else ""
        except Exception as e:
            raise RuntimeError(f"Intelligence Engine communication error: {str(e)}")
