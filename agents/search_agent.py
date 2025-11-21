import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from utils.prompts import SEARCH_SYSTEM_PROMPT # <--- Import

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class SearchAgent:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"
        
        self.google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

    def research(self, query: str):
        print(f"🔎 Search Agent is looking up: '{query}'...")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=query,
                    config=types.GenerateContentConfig(
                        tools=[self.google_search_tool],
                        response_modalities=["TEXT"],
                        system_instruction=SEARCH_SYSTEM_PROMPT # <--- INJECT PERSONA HERE
                    )
                )
                return response.text

            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if "429" in str(e):
                    time.sleep(2) 
                else:
                    return f"Error performing search: {str(e)}"
        
        return "Error: Search failed after maximum retries."

if __name__ == "__main__":
    agent = SearchAgent()
    print(agent.research("Who won the 2024 Nobel Prize in Physics?"))