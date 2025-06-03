from typing import Dict, List, Any, Optional
from openai import OpenAI
from model.embeddings import IntentEmbeddings
from protocol.portfolio_services import PortfolioServices
from model.context import PortfolioAssistantContext
import json
from config import OPENAI_API_KEY, MODEL_NAME

class LLMProcessor:
    def __init__(self):
        """Initialize LLM processor with OpenAI client and embeddings."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.embeddings = IntentEmbeddings()
        self.portfolio_services = PortfolioServices()
        
        # Load function definitions
        with open('model/intent_map.json', 'r') as f:
            self.functions = json.load(f)
    
    def process_query(self, user_input: str) -> str:
        """
        Main processing pipeline for user queries.
        
        Args:
            user_input: The user's natural language query
            
        Returns:
            str: Natural language response to the user's query
        """
        print("--------------------------------we are in process_query--------------------------------")
        try:
            # 1. Find matching intents
            matches = self.embeddings.find_closest_intent(user_input, top_k=2)

            print("matches------------\n\n\n",matches)
            
            if not matches:
                return "I'm sorry, but I couldn't understand your request. Could you please rephrase it?"
            
            # 2. If confidence is too low, ask for clarification
            if matches[0]['similarity'] < 0.50:
                return self.handle_low_confidence(user_input, matches)
            
            # 3. Prepare function calling format
            functions = self.prepare_functions(matches)
            
            if not functions:
                return "I apologize, but I couldn't find appropriate functions to handle your request."
            
            # 4. Make LLM call for function selection and parameter extraction
            completion = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    PortfolioAssistantContext.get_context(),
                    {"role": "user", "content": user_input}
                ],
                functions=functions,
                function_call={"name": matches[0]["tool_name"]}
            )
            
            print("\n\n\ncompletion------------\n\n\n",completion)
            
            # 5. Extract function call details
            function_call = completion.choices[0].message.function_call
            print("\n\n\nfunction_call------------\n\n\n",function_call)
            if not function_call:
                return "I apologize, but I couldn't determine how to process your request."
            
            # 6. Execute the function
            result = self.execute_function(
                function_call.name,
                json.loads(function_call.arguments)
            )
            
            # 7. Generate natural language response
            response = self.generate_response(result, user_input, function_call.name)
            
            return response
            
        except Exception as e:
            print(f"Error in process_query: {str(e)}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    def prepare_functions(self, matches: List[Dict]) -> List[Dict]:
        """
        Prepare the function definitions for OpenAI's function calling format.
        Only uses the highest similarity match.
        """
        print("--------------------------------we are in prepare_functions--------------------------------")
        prepared_functions = []
        
        # Only use the highest similarity match
        best_match = matches[0]  # Since matches are already sorted by similarity
        print("\n\n\nbest_match------------\n\n\n",best_match)

        
        function_def = next(
            (f for f in self.functions if f["name"] == best_match["tool_name"]),
            None
        )
        print("\n\n\nfunction_def------------\n\n\n",function_def)
        if function_def:
            prepared_functions.append(function_def)
            
        print("\n\n\nprepared_functions------------\n\n\n",prepared_functions)
        return prepared_functions
    
    def execute_function(self, function_name: str, parameters: Dict) -> Any:
        """
        Execute the matched function with extracted parameters.
        """
        print("--------------------------------we are in execute_function--------------------------------")
        # Map function names to portfolio service methods
        function_map = {
            "get_stock_price": self.portfolio_services.get_stock_price,
            "get_total_portfolio_value": self.portfolio_services.get_total_portfolio_value,
            "get_invested_sectors": self.portfolio_services.get_invested_sectors,
            "get_sector_holdings": self.portfolio_services.get_sector_holdings,
            "compare_stocks": self.portfolio_services.compare_stocks,
            "get_portfolio_summary": self.portfolio_services.get_portfolio_summary
        }
        
        if function_name not in function_map:
            raise ValueError(f"Unknown function: {function_name}")
        
        # Handle parameter conversions
        if function_name == "get_stock_price":
            # Ensure tickers is always a list
            if isinstance(parameters.get('tickers'), str):
                parameters['tickers'] = [parameters['tickers']]
        elif function_name == "get_sector_holdings":
            # Ensure sectors is always a list
            if isinstance(parameters.get('sectors'), str):
                parameters['sectors'] = [parameters['sectors']]
        elif function_name == "compare_stocks":
            # Map stock1 and stock2 to the function's parameters
            return function_map[function_name](
                stock1=parameters.get('stock1'),
                stock2=parameters.get('stock2')
            )
            
        return function_map[function_name](**parameters)
    
    def generate_response(self, result: Any, original_query: str, function_name: str) -> str:
        """
        Generate a natural language response based on the function result.
        """
        print("--------------------------------we are in generate_response--------------------------------")
        # Create a prompt for response generation
        completion = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                PortfolioAssistantContext.get_context(),
                {"role": "user", "content": original_query},
                {"role": "assistant", "content": f"Here's the data from {function_name}: {json.dumps(result)}"}
            ]
        )
        
        return completion.choices[0].message.content
    
    def handle_low_confidence(self, query: str, matches: List[Dict]) -> str:
        """
        Handle cases where intent matching confidence is low.
        """
        print("--------------------------------we are in handle_low_confidence--------------------------------")
        response = "I'm not quite sure what you're asking about. Are you trying to:\n"
        for match in matches:
            response += f"- {match['description']}\n"
        response += "\nCould you please rephrase your question?"
        return response
