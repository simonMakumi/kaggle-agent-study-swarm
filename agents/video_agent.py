import os
import time
from dotenv import load_dotenv
from google import genai
from utils.prompts import VIDEO_SYSTEM_PROMPT

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class VideoAgent:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"

    def analyze_video(self, video_path: str, question: str):
        """
        Uploads a video file and asks Gemini questions about it.
        """
        print(f"🎥 Video Agent is watching: {video_path}...")

        try:
            video_file = self.client.files.upload(file=video_path)
            
            # 2. Wait for processing (Big files take a few seconds)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state.name == "FAILED":
                return "⚠️ Video processing failed."

            # 3. Ask the question using the System Prompt
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[video_file, VIDEO_SYSTEM_PROMPT, question]
            )
            
            return response.text

        except Exception as e:
            return f"Error analyzing video: {str(e)}"