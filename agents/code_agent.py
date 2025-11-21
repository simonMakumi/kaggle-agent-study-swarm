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
            
            # CONSTRUCT THE FULL ANSWER MANUALLY
            # This ensures we see the Code AND the Result
            final_output = ""
            
            if not response.candidates:
                return "⚠️ No response generated."

            for part in response.candidates[0].content.parts:
                # 1. If it's text (Explanation)
                if part.text:
                    final_output += part.text + "\n\n"
                
                # 2. If it's code (The script)
                elif part.executable_code:
                    final_output += f"```python\n{part.executable_code.code}\n```\n"
                
                # 3. If it's the result (The number!)
                elif part.code_execution_result:
                    # We wrap the result in a nice bold block
                    output = part.code_execution_result.output
                    final_output += f"**> Execution Result:**\n```\n{output}\n```\n"

            return final_output

        except Exception as e:
            return f"Error executing code: {str(e)}"

if __name__ == "__main__":
    agent = CodeAgent()
    print(agent.solve("Calculate the area of a circle with radius 5"))