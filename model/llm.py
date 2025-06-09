from typing import Dict, List, Any, Optional
import json
import logging
import asyncio
from openai import AsyncOpenAI

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import Tool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from model.embeddings import IntentEmbeddings
from protocol.portfolio_services import PortfolioServices
from model.context import PortfolioAssistantContext
from model.tool_configs import get_tool_configs
from config import OPENAI_API_KEY, MODEL_NAME

# Set up logging
logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self):
        """Initialize LLM processor with OpenAI client and embeddings."""
        logger.info("Initializing LLMProcessor...")
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.embeddings = IntentEmbeddings()
        self.portfolio_services = PortfolioServices()
        
        # Load function definitions
        with open('model/intent_map.json', 'r') as f:
            self.functions = json.load(f)
            
        self.tools = self._prepare_langchain_tools()
        self.llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
        self.agent_executor = None

    def _prepare_langchain_tools(self) -> List[Tool]:
        """Convert our existing functions to LangChain tools."""
        print("--------------------------------we are in _prepare_langchain_tools--------------------------------")
        tools = []
        
        # Get tool configurations
        tool_configs = get_tool_configs(self.portfolio_services)
        
        for func in self.functions:
            try:
                func_name = func["name"]
                if func_name not in tool_configs:
                    logger.warning(f"No configuration found for {func_name}")
                    continue
                    
                config = tool_configs[func_name]
                
                if config["has_params"]:
                    # For functions with parameters
                    tool = StructuredTool.from_function(
                        name=func_name,
                        description=func["description"],
                        func=config["method"],
                        args_schema=config["model"]
                    )
                else:
                    # For functions without parameters, wrap in a lambda that ignores any args
                    tool = Tool(
                        name=func_name,
                        description=func["description"],
                        func=config["method"]
                    )
                    
                tools.append(tool)
                
            except Exception as e:
                logger.error(f"Error creating tool for {func['name']}: {str(e)}")
                continue
                
        return tools

    async def setup_agent(self):
        """Set up the LangChain agent using our existing context."""
        print("--------------------------------we are in setup_agent--------------------------------")
        if self.agent_executor is not None:
            return

        # Use our existing context
        system_message = PortfolioAssistantContext.BASE_CONTEXT
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    async def process_query(self, user_input: str) -> str:
        """Process user queries using LangChain while maintaining our existing logic."""
        print("--------------------------------we are in process_query--------------------------------")
        try:
            # Use our existing embeddings for intent matching
            matches = await asyncio.to_thread(
                self.embeddings.find_closest_intent, 
                user_input, 
                top_k=2
            )

            if not matches:
                return "I'm sorry, but I couldn't understand your request. Could you please rephrase it?"

            if matches[0]['similarity'] < 0.50:
                return self.handle_low_confidence(user_input, matches)

            # Ensure agent is set up
            if self.agent_executor is None:
                await self.setup_agent()

            # Use LangChain for processing
            response = await self.agent_executor.ainvoke({"input": user_input})
            return response["output"]

        except Exception as e:
            logger.error(f"Error in process_query: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def handle_low_confidence(self, query: str, matches: List[Dict]) -> str:
        """Handle cases where intent matching confidence is low."""
        print("--------------------------------we are in handle_low_confidence--------------------------------")
        logger.info(f"Handling low confidence for query: '{query}'")
        response = "I'm not quite sure what you're asking about. Are you trying to:\n"
        for match in matches:
            response += f"- {match['description']}\n"
        response += "\nCould you please rephrase your question?"
        return response
