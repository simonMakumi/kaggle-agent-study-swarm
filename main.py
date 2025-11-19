import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown

# Import our specialist agents
from agents.search_agent import SearchAgent
from agents.doc_agent import DocAgent
from agents.code_agent import CodeAgent

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Rich Console
console = Console()

class StudyManager:
    def __init__(self):
        # Show a cool loading sequence
        console.print(Panel.fit("[bold cyan]🐝 Study Swarm Agent[/bold cyan]", border_style="cyan"))
        console.print("[italic dim]Initializing System...[/italic dim]")
        
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"
        
        with console.status("[bold yellow]Waking up agents...[/bold yellow]", spinner="dots"):
            self.search_agent = SearchAgent()
            self.doc_agent = DocAgent()
            self.code_agent = CodeAgent()
            time.sleep(1.5) # Fake delay just for the cool visual effect
        
        console.print("[bold green]✅ System Online.[/bold green]")
        
        # Simple Session Memory
        self.current_pdf = None

    def route_query(self, query: str) -> str:
        """
        Uses Gemini to decide which agent should handle the user's request.
        """
        prompt = f"""
        You are the Manager of a Study Swarm. You have three specialists:
        1. SEARCH: For real-time news, facts, definitions, or general knowledge.
        2. DOC: ONLY for questions specifically about the uploaded PDF document.
        3. CODE: For math, logic puzzles, or writing/running Python code.
        4. CHAT: For general greetings or conversation that doesn't need a tool.

        User Query: "{query}"
        Current PDF Loaded: {self.current_pdf}

        Return ONLY one word: SEARCH, DOC, CODE, or CHAT.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip().upper().replace("\n", "").replace(".", "")
        except Exception:
            return "CHAT"

    def run(self):
        console.print("\n[bold white]🎓 Study Swarm is ready![/bold white]")
        console.print("I can [bold blue]Search the web 🌐[/bold blue], [bold red]Read PDFs 📄[/bold red], or [bold green]Run Code 💻[/bold green].")
        
        # Ask for PDF with Rich Prompt
        pdf_input = Prompt.ask("\n[bold yellow]📂 PDF Path[/bold yellow] (Press Enter to skip)")
        
        if pdf_input:
            if os.path.exists(pdf_input):
                self.current_pdf = pdf_input
                console.print(f"[green]✅ Loaded:[/green] {self.current_pdf}")
            else:
                console.print(f"[red]⚠️ File not found:[/red] {pdf_input}. Proceeding without PDF.")
                self.current_pdf = "test_notes.pdf" 

        console.print("[dim]Type 'quit' to exit.[/dim]\n")

        while True:
            user_input = Prompt.ask("[bold cyan]User[/bold cyan]")
            
            if user_input.lower() in ['quit', 'exit']:
                console.print("[bold violet]👋 Keep studying! Goodbye.[/bold violet]")
                break
            
            if not user_input:
                continue
                
            # 1. ROUTE: Decide who handles it
            with console.status("[bold yellow]🤔 Manager is thinking...[/bold yellow]", spinner="earth"):
                route = self.route_query(user_input)
                time.sleep(0.5) # Brief pause for effect
            
            console.print(f"   [dim]↳ Routing to:[/dim] [bold magenta]{route}[/bold magenta]")
            
            response = ""
            
            # 2. DELEGATE
            try:
                if route == "DOC":
                    if self.current_pdf:
                        with console.status("[bold red]📄 Reading Document...[/bold red]"):
                            response = self.doc_agent.ask_pdf(self.current_pdf, user_input)
                    else:
                        response = "I need a PDF loaded to answer that! Please restart and provide a path."
                        
                elif route == "SEARCH":
                    with console.status("[bold blue]🌐 Searching Google...[/bold blue]"):
                        response = self.search_agent.research(user_input)
                    
                elif route == "CODE":
                    # Code agent handles its own printing, so we just call it
                    response = self.code_agent.solve(user_input)
                    
                else:
                    # General Chat
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=f"You are a helpful study assistant. Keep it brief. Reply to: {user_input}"
                    ).text
            except Exception as e:
                response = f"⚠️ An error occurred: {e}"

            # 3. SHOW RESULT
            # If the route was CODE, it already printed the fancy boxes.
            # If it was SEARCH, DOC, or CHAT, we print the text in a Panel.
            if route != "CODE":
                console.print(Panel(Markdown(response), title="🐝 Swarm Answer", border_style="green"))
            
            console.print("\n") # Spacing

if __name__ == "__main__":
    manager = StudyManager()
    manager.run()