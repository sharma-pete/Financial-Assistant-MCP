from dotenv import load_dotenv
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('portfolio_assistant.log')
    ]
)

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Validate required environment variables
def validate_env():
    """Validate that all required environment variables are set."""
    required_vars = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "MODEL_NAME": MODEL_NAME,
        "PINECONE_API_KEY": PINECONE_API_KEY,
        "PINECONE_ENVIRONMENT": PINECONE_ENVIRONMENT,
        "PINECONE_INDEX": PINECONE_INDEX,
        "PINECONE_CLOUD": PINECONE_CLOUD,
        "DATABASE_URL": DATABASE_URL
    }

    # for name,var in required_vars.items():
    #     print(f"{name}: {var}")

    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please ensure these are set in your .env file."
        )

# Validate environment variables on import
validate_env()
