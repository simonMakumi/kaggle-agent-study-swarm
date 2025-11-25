import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from utils.prompts import DOC_SYSTEM_PROMPT

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.pdf_tool import read_pdf

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class DocAgent:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"

    def ask_pdf(self, pdf_path: str, question: str):
        pdf_text = read_pdf(pdf_path)

        full_prompt = f"""
        {DOC_SYSTEM_PROMPT}
        
        DOCUMENT CONTENT:
        {pdf_text}
        
        USER QUESTION:
        {question}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            return f"Error processing document: {str(e)}"

# --- Test Block ---
if __name__ == "__main__":
    # To test this, we need a dummy PDF.
    test_pdf_name = "test_notes.pdf"
    if not os.path.exists(test_pdf_name):
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Secret Project: The codename is 'Blue Sky'. The launch date is Jan 2026.")
        doc.save(test_pdf_name)
        print(f"Created dummy file: {test_pdf_name}")

    agent = DocAgent()
    answer = agent.ask_pdf(test_pdf_name, "What is the codename of the project?")
    print("\n--- Result ---")
    print(answer)
