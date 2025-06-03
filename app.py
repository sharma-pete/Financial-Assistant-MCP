from data_loader import DataLoader
from protocol.portfolio_services import PortfolioServices
from model.embeddings import IntentEmbeddings
from model.llm import LLMProcessor
import sys
from functools import wraps
from typing import Callable, Dict

def command(name: str) -> Callable:
    """Decorator to register commands."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        wrapper.is_command = True
        wrapper.command_name = name
        return wrapper
    return decorator

class PortfolioApp:
    def __init__(self):
        """Initialize the Portfolio Application."""
        self.loader = DataLoader()
        self.portfolio = None
        self.commands: Dict[str, Callable] = {}
        
        # Register all methods decorated with @command
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, 'is_command'):
                self.commands[attr.command_name] = attr

    def run(self, command_name: str = None):
        """Execute the specified command or show available commands."""
        if command_name is None:
            print("Available commands:")
            for cmd in self.commands:
                print(f"- {cmd}")
            return

        if command_name not in self.commands:
            print(f"Unknown command: {command_name}")
            print("Available commands:")
            for cmd in self.commands:
                print(f"- {cmd}")
            sys.exit(1)

        self.commands[command_name]()

    @command('setup')
    def initialize(self):
        """Initialize the application by loading data and setting up services."""
        print("Initializing Portfolio Analysis System...")
        try:
            # Load all CSV files into the database
            print("Loading data from CSV files...")
            self.loader.load_csv_files()
            print("Data loaded successfully!")

            # Initialize embeddings
            print("Initializing embeddings...")
            self.embeddings = IntentEmbeddings()
            self.embeddings.upload_intents('model/intent_map.json')
            print("Embeddings initialized!")

            # Upload intents to Pinecone
            # Initialize portfolio services
            self.portfolio = PortfolioServices()
            print("Portfolio services initialized!")
            print("\nSetup complete! You can now use 'python app.py chat' to start the chat interface.")
            
        except Exception as e:
            print(f"Error initializing application: {str(e)}")
            sys.exit(1)

    @command('chat')
    def run_chat(self):
        """Run the chat interface."""
        if self.portfolio is None:
            self.portfolio = PortfolioServices()
        
        # Initialize LLM processor
        self.llm_processor = LLMProcessor()
        
        print("\nStarting chat interface...")
        print("Type 'exit' to quit the application")
        print("You can ask questions about your portfolio, get insights, or request analysis.")
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'exit':
                print("\nExiting Portfolio Analysis System...")
                break
                
            if not user_input:
                continue
            
            # Process through LLM pipeline
            response = self.llm_processor.process_query(user_input)
            print("\nAssistant:", response)

if __name__ == "__main__":
    app = PortfolioApp()
    command_name = sys.argv[1] if len(sys.argv) > 1 else None
    app.run(command_name) 