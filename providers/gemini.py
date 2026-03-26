import os
from .base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it to use Gemini.")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except ImportError:
            raise ImportError("google-generativeai package is not installed. Please install it.")

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            # handle case where text is potentially empty or blocked
            if getattr(response, 'text', None):
                return response.text.strip()
            # fallback if 'parts' structure differs
            return response.parts[0].text.strip() if response.parts else ""
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
