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

# Import Agents
from agents.search_agent import SearchAgent
from agents.doc_agent import DocAgent
from agents.code_agent import CodeAgent
from agents.video_agent import VideoAgent # <--- NEW

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

console = Console()

class StudyManager:
    def __init__(self):
        console.print(Panel.fit("[bold cyan]🐝 Study Swarm Agent 2.0[/bold cyan]", border_style="cyan"))
        
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"
        
        with console.status("[bold yellow]Waking up agents...[/bold yellow]", spinner="dots"):
            self.search_agent = SearchAgent()
            self.doc_agent = DocAgent()
            self.code_agent = CodeAgent()
            self.video_agent = VideoAgent() # <--- NEW
            time.sleep(1) 
        
        console.print("[bold green]✅ System Online.[/bold green]")
        
        self.current_pdf = None
        self.current_video = None # <--- NEW

    def route_query(self, query: str) -> str:
        """
        Decides which agent to use. Includes Retry Logic for 429 Errors.
        """
        prompt = f"""
        You are the Manager of a Study Swarm.
        1. SEARCH: Real-time news, facts, definitions.
        2. DOC: Questions about the uploaded PDF ({self.current_pdf}).
        3. VIDEO: Questions about the uploaded Video ({self.current_video}).
        4. CODE: Math, logic, python code.
        5. CHAT: General greetings/conversation.

        User Query: "{query}"
        
        Return ONLY one word: SEARCH, DOC, VIDEO, CODE, or CHAT.
        """
        
        # Retry Loop for robustness
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text.strip().upper().replace("\n", "").replace(".", "")
            except Exception as e:
                if "429" in str(e):
                    time.sleep(2) # Wait a bit if overloaded
                    continue
                return "CHAT" # Fallback
        return "CHAT"

    def run(self):
        console.print("\n[bold white]🎓 Study Swarm is ready![/bold white]")
        console.print("I can [blue]Search 🌐[/blue], [red]Read PDFs 📄[/red], [magenta]Watch Videos 🎥[/magenta], or [green]Run Code 💻[/green].")
        
        # 1. Ask for PDF
        pdf_input = Prompt.ask("\n[bold yellow]📂 PDF Path[/bold yellow] (Enter to skip)")
        if pdf_input and os.path.exists(pdf_input):
            self.current_pdf = pdf_input
            console.print(f"[green]✅ Loaded PDF:[/green] {self.current_pdf}")

        # 2. Ask for Video (NEW)
        video_input = Prompt.ask("[bold magenta]🎥 Video Path[/bold magenta] (Enter to skip)")
        if video_input and os.path.exists(video_input):
            self.current_video = video_input
            console.print(f"[green]✅ Loaded Video:[/green] {self.current_video}")

        console.print("\n[dim]Type 'quit' to exit.[/dim]")

        while True:
            user_input = Prompt.ask("\n[bold cyan]User[/bold cyan]")
            
            if user_input.lower() in ['quit', 'exit']:
                console.print("[bold violet]👋 Goodbye.[/bold violet]")
                break
            
            if not user_input: continue
                
            # ROUTING
            with console.status("[bold yellow]🤔 Routing...[/bold yellow]"):
                route = self.route_query(user_input)
            
            console.print(f"   [dim]↳ Routing to:[/dim] [bold magenta]{route}[/bold magenta]")
            
            response = ""
            try:
                if route == "DOC":
                    if self.current_pdf:
                        with console.status("[bold red]📄 Reading...[/bold red]"):
                            response = self.doc_agent.ask_pdf(self.current_pdf, user_input)
                    else:
                        response = "No PDF loaded."

                elif route == "VIDEO":
                    if self.current_video:
                        # Video agent handles its own status spinner
                        response = self.video_agent.analyze_video(self.current_video, user_input)
                    else:
                        response = "No Video loaded."
                        
                elif route == "SEARCH":
                    with console.status("[bold blue]🌐 Searching...[/bold blue]"):
                        response = self.search_agent.research(user_input)
                    
                elif route == "CODE":
                    response = self.code_agent.solve(user_input)
                    
                else:
                    # General Chat
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=f"Reply briefly: {user_input}"
                    ).text
                    
            except Exception as e:
                response = f"⚠️ Error: {e}"

            if route != "CODE":
                console.print(Panel(Markdown(response), title="🐝 Swarm Answer", border_style="green"))

if __name__ == "__main__":
    manager = StudyManager()
    manager.run()