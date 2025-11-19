import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class CodeAgent:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"
        self.console = Console()

    def solve(self, problem: str):
        """
        Generates code, runs it, and formats the output beautifully.
        """
        self.console.print(f"[bold blue]💻 Code Agent is solving:[/bold blue] {problem}...")
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=problem,
                config=types.GenerateContentConfig(
                    tools=[{'code_execution': {}}],
                    response_modalities=["TEXT"]
                )
            )
            
            # We need to handle the response parts manually to make it look good
            final_answer = ""
            
            # Loop through every part of the agent's thought process
            for part in response.candidates[0].content.parts:
                
                # 1. If it's Python Code...
                if part.executable_code:
                    code = part.executable_code.code
                    # Print nicely formatted syntax-highlighted code
                    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
                    self.console.print(Panel(syntax, title="🐍 Generated Python Code", border_style="cyan"))
                
                # 2. If it's the Execution Result...
                elif part.code_execution_result:
                    output = part.code_execution_result.output
                    # Print the computer's output in a green box
                    self.console.print(Panel(output, title="⚙️ Execution Output", border_style="green"))
                
                # 3. If it's Text (Explanation)...
                elif part.text:
                    # We collect the text to return it, but we don't print it here 
                    # to avoid cluttering the screen before the final summary.
                    final_answer += part.text

            return final_answer

        except Exception as e:
            return f"Error executing code: {str(e)}"

if __name__ == "__main__":
    agent = CodeAgent()
    # Test with something that requires calculation
    result = agent.solve("Calculate the first 10 numbers of the Fibonacci sequence")
    print("\n--- Final Answer ---")
    print(result)