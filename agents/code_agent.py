import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from utils.prompts import CODE_SYSTEM_PROMPT

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class CodeAgent:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"

    def solve(self, problem: str):
        print(f"💻 Code Agent is solving: '{problem}'...")
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=problem,
                config=types.GenerateContentConfig(
                    tools=[{'code_execution': {}}],
                    response_modalities=["TEXT"], 
                    system_instruction=CODE_SYSTEM_PROMPT
                )
            )
            
            result_package = {
                "text": "",
                "images": []
            }
            
            if not response.candidates:
                result_package["text"] = "⚠️ No response generated."
                return result_package

            print(f"   -> Received {len(response.candidates[0].content.parts)} parts from Gemini.")

            for part in response.candidates[0].content.parts:
                
                if part.text:
                    result_package["text"] += part.text + "\n\n"
                
                elif part.executable_code:
                    print("   -> Code block detected.")
                    result_package["text"] += f"```python\n{part.executable_code.code}\n```\n"
                
                elif part.code_execution_result:
                    print("   -> Execution Result detected.")
                    output = part.code_execution_result.output
                    result_package["text"] += f"**> Execution Result:**\n```\n{output}\n```\n"
                
                # Check for images
                if hasattr(part, "inline_data") and part.inline_data:
                    print("   -> Graph detected! 📊")
                    result_package["images"].append(part.inline_data)

            return result_package

        except Exception as e:
            return {"text": f"Error executing code: {str(e)}", "images": []}

if __name__ == "__main__":
    agent = CodeAgent()
    # Test with a graphing prompt
    res = agent.solve("Plot a sine wave from 0 to 10 using matplotlib")
    print(res["text"])
    if res["images"]:
        print(f"Found {len(res['images'])} images.")