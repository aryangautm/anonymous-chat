from google.genai import Client

from app.core.config import settings

genai_client = Client(api_key=settings.GEMINI_API_KEY)
