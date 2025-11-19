import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class SearchAgent:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        # CHANGED: Switch to 1.5-flash for stability and better free tier limits
        self.model_name = "gemini-2.0-flash" 
        
        self.google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

    def research(self, query: str):
        print(f"🔎 Search Agent is looking up: '{query}'...")

        # RETRY LOGIC: Try 3 times before failing
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=query,
                    config=types.GenerateContentConfig(
                        tools=[self.google_search_tool],
                        response_modalities=["TEXT"]
                    )
                )
                return response.text

            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    # Wait 5 seconds before retrying
                    time.sleep(5) 
                else:
                    # If it's not a rate limit error, raise it immediately
                    return f"Error performing search: {str(e)}"
        
        return "Error: Search failed after maximum retries."

if __name__ == "__main__":
    agent = SearchAgent()
    # Let's try a query that requires real-time info to prove the tool works
    result = agent.research("Who won the 2024 Nobel Prize in Physics?")
    print("\n--- Result ---")
    print(result)