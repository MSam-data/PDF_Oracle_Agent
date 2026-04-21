import os
import time
from PyPDF2 import PdfReader
from google import genai
from google.api_core import exceptions

class PDFOracleEngine:
    def __init__(self):
        self.client = None
        self.active_model = None
        # Load keys from environment
        raw_keys = [os.getenv("GOOGLE_API_KEY"), os.getenv("GOOGLE_API_KEY_2")]
        self.api_keys = [k for k in raw_keys if k]

    def initialize_ai(self):
        """
        Tests API keys and models to find a working pair.
        Returns a status message for the Frontend.
        """
        if not self.api_keys:
            return "❌ Error: No API keys found in .env"

        priority_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        for i, key in enumerate(self.api_keys):
            try:
                temp_client = genai.Client(api_key=key)
                for model_name in priority_models:
                    try:
                        # Prevent instant 429 on startup
                        time.sleep(1) 
                        temp_client.models.generate_content(model=model_name, contents="ping")
                        
                        # Setting global state for this session
                        self.client = temp_client
                        self.active_model = model_name
                        return f"🚀 AI Online! Key_{i} verified ({model_name})"
                    except Exception as e:
                        if "429" in str(e):
                            break # Move to next key
                        continue
            except Exception:
                continue
        return "❌ CRITICAL: All API keys failed or rate-limited."

    def extract_text(self, pdf_path):
        """Extracts text from the uploaded PDF file."""
        text = ""
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def query(self, pdf_text, user_prompt):
        """Sends the document context and user question to the AI."""
        if not self.client:
            return "AI Infrastructure not initialized."
            
        system_instruction = (
            "You are a PDF Oracle. Your goal is to answer questions based ONLY on the provided text. "
            "If the information is missing, say 'I cannot find that in the document.'\n\n"
            f"DOCUMENT CONTEXT:\n{pdf_text[:20000]}" # Safety cap for token limits
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.active_model,
                contents=f"{system_instruction}\n\nUSER QUESTION: {user_prompt}"
            )
            return response.text
        except exceptions.ResourceExhausted:
            return "⏳ Rate limit (429) hit. Please wait a few seconds."
        except Exception as e:
            return f"AI Error: {str(e)}"