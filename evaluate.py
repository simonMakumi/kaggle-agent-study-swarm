import os
import time
import json
from dotenv import load_dotenv
from google import genai
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

# Import Agents
from agents.search_agent import SearchAgent
from agents.code_agent import CodeAgent
from agents.doc_agent import DocAgent

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
console = Console()

class AIJudge:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.0-flash"
        
        # Initialize Agents to be tested
        self.search_agent = SearchAgent()
        self.code_agent = CodeAgent()
        self.doc_agent = DocAgent()

    def create_test_pdf(self):
        """Creates a dummy PDF for the Doc Agent test."""
        filename = "eval_test.pdf"
        if not os.path.exists(filename):
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            text = """
            CONFIDENTIAL REPORT
            Subject: Project Apollo 2.0
            Date: 2025-11-21
            Budget: $500 Million
            The goal of Project Apollo 2.0 is to establish a permanent base on Mars.
            The primary contractor is SpaceX.
            """
            page.insert_text((50, 50), text)
            doc.save(filename)
        return filename

    def get_judge_score(self, query, response, criteria):
        """Asks Gemini to grade the response."""
        judge_prompt = f"""
        You are an AI Quality Assurance Judge. 
        
        USER QUERY: "{query}"
        AGENT RESPONSE: "{response}"
        
        CRITERIA: {criteria}
        
        INSTRUCTIONS:
        1. Rate the response on a scale of 1 to 5.
        2. 1 = Terrible/Wrong, 5 = Perfect.
        3. Provide a brief 1-sentence explanation.
        
        FORMAT:
        SCORE: [number]
        REASON: [explanation]
        """
        
        try:
            eval_resp = self.client.models.generate_content(
                model=self.model_name,
                contents=judge_prompt
            ).text
            return eval_resp
        except:
            return "SCORE: 0\nREASON: Evaluation Failed."

    def run_evals(self):
        console.print(Panel.fit("[bold magenta]🤖 AI Evaluation Pipeline[/bold magenta]", border_style="magenta"))
        
        # 1. Setup Data
        pdf_path = self.create_test_pdf()
        
        test_cases = [
            {
                "type": "SEARCH",
                "query": "Who is the current CEO of Google?",
                "agent": self.search_agent,
                "criteria": "Must be accurate (Sundar Pichai) and recent."
            },
            {
                "type": "CODE",
                "query": "Calculate the factorial of 5 using Python.",
                "agent": self.code_agent,
                "criteria": "Must include Python code AND the correct execution result (120)."
            },
            {
                "type": "DOC",
                "query": "What is the budget for Project Apollo 2.0?",
                "agent": self.doc_agent,
                "pdf": pdf_path, 
                "criteria": "Must extract '$500 Million' from the provided PDF text."
            }
        ]

        results = []

        # 2. Run Tests
        for test in track(test_cases, description="Running Tests..."):
            try:
                # A. Get Agent Response
                if test["type"] == "SEARCH":
                    response = test["agent"].research(test["query"])
                elif test["type"] == "CODE":
                    # Handle the dict response from code agent
                    res_pkg = test["agent"].solve(test["query"])
                    response = res_pkg["text"] 
                elif test["type"] == "DOC":
                    response = test["agent"].ask_pdf(test["pdf"], test["query"])
                
                # B. Judge Response
                evaluation = self.get_judge_score(test["query"], response, test["criteria"])
                
                # C. Parse Score
                score_line = [line for line in evaluation.split('\n') if "SCORE:" in line][0]
                score = int(score_line.split(":")[1].strip())
                
                results.append({
                    "Type": test["type"],
                    "Query": test["query"],
                    "Score": score,
                    "Evaluation": evaluation
                })
                
            except Exception as e:
                results.append({
                    "Type": test["type"],
                    "Query": test["query"],
                    "Score": 0,
                    "Evaluation": f"Error: {str(e)}"
                })

        # 3. Print Report
        table = Table(title="📊 Evaluation Report")
        table.add_column("Agent", style="cyan")
        table.add_column("Query", style="white")
        table.add_column("Score", style="bold green")
        table.add_column("Judge's Reason", style="yellow")

        total_score = 0
        for res in results:
            reason = [line for line in res["Evaluation"].split('\n') if "REASON:" in line]
            reason_text = reason[0].replace("REASON: ", "") if reason else "No reason provided"
            
            # Color code the score
            score_display = f"[green]{res['Score']}/5[/green]" if res['Score'] >= 4 else f"[red]{res['Score']}/5[/red]"
            
            table.add_row(res["Type"], res["Query"], score_display, reason_text)
            total_score += res["Score"]

        console.print(table)
        
        avg = total_score / len(test_cases)
        console.print(f"\n[bold white]📈 Average System Reliability:[/bold white] [bold blue]{avg:.1f}/5.0[/bold blue]")
        
        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    judge = AIJudge()
    judge.run_evals()
