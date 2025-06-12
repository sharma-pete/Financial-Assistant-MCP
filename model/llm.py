from typing import Dict, List, Any, Optional
import json
import logging
import asyncio
from openai import AsyncOpenAI

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import Tool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from model.embeddings import IntentEmbeddings
from protocol.portfolio_services import PortfolioServices
from model.context import PortfolioAssistantContext
from model.tool_configs import get_tool_configs
from config import OPENAI_API_KEY, MODEL_NAME

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self):
        """Initialize LLM processor with OpenAI client and embeddings."""
        logger.info("Initializing LLMProcessor...")
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.embeddings = IntentEmbeddings()
        self.portfolio_services = PortfolioServices()
        
        with open('model/intent_map.json', 'r') as f:
            self.functions = json.load(f)
            
        self.tools = self._prepare_langchain_tools()
        self.llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
        self.agent_executor = None

    def _prepare_langchain_tools(self) -> List[Tool]:
        """Convert our existing functions to LangChain tools."""
        tools = []
        
        tool_configs = get_tool_configs(self.portfolio_services)
        
        for func in self.functions:
            try:
                func_name = func["name"]
                if func_name not in tool_configs:
                    logger.warning(f"No configuration found for {func_name}")
                    continue
                    
                config = tool_configs[func_name]
                
                tool = StructuredTool.from_function(
                    name=func_name,
                    description=func["description"],
                    func=config["method"],
                    args_schema=config["model"]
                )
                
                tools.append(tool)
                
            except Exception as e:
                logger.error(f"Error creating tool for {func['name']}: {str(e)}")
                continue
                
        return tools

    async def setup_agent(self):
        """Set up the LangChain agent using our existing context."""
        if self.agent_executor is not None:
            return

        system_message = PortfolioAssistantContext.BASE_CONTEXT
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    async def execute_tool(self, user_input: str) -> Optional[str]:
        """Execute a tool and return its response."""
        try:
            if self.agent_executor is None:
                await self.setup_agent()
            result = await self.agent_executor.ainvoke({"input": user_input})
            return result.get("output")
        except Exception as e:
            logger.error(f"Error executing tool: {str(e)}")
            return None

    async def process_query(self, user_input: str) -> str:
        """Process user queries using LangChain while maintaining our existing logic."""
        try:
            query = user_input.strip().lower()
            
            matches = await asyncio.to_thread(
                self.embeddings.find_closest_intent, 
                query,
                top_k=3
            )

            if not matches:
                return "I'm sorry, but I couldn't understand your request. Could you please rephrase it?"

            best_match = matches[0]
            similarity = best_match['similarity']

            if similarity >= 0.45:
                response = await self.execute_tool(user_input)
                return response if response else "I encountered an error processing your request."
            
            elif similarity >= 0.25:
                responses = ["Let me explore a few possibilities based on your request..."]
                executed_tools = set()
                
                for match in matches:
                    if match['similarity'] >= 0.25 and match['tool_name'] not in executed_tools:
                        executed_tools.add(match['tool_name'])
                        response = await self.execute_tool(user_input)
                        if response:
                            responses.append(f"\nTrying {match['tool_name']} (confidence: {match['similarity']:.2f}):")
                            responses.append(response)
                
                if len(responses) > 1:
                    return "\n".join(responses)
                return self.handle_low_confidence(user_input, matches)
            
            else:
                return self.handle_low_confidence(user_input, matches)

        except Exception as e:
            logger.error(f"Error in process_query: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def handle_low_confidence(self, query: str, matches: List[Dict]) -> str:
        """Handle cases where intent matching confidence is low."""
        logger.info(f"Handling low confidence for query: '{query}'")
        
        response = [
            "I'm not entirely sure what you're asking for. Here are some possibilities:",
            ""
        ]
        
        for match in matches:
            confidence = match['similarity']
            response.append(f"- {match['description']}")
            response.append(f"  Example: {match['example']}")
            response.append(f"  Confidence: {confidence:.2f}")
            response.append("")
        
        response.append("Could you please rephrase your question to match one of these patterns?")
        return "\n".join(response)
