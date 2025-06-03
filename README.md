# Financial Assistant with Multi-Portfolio Capabilities

A sophisticated financial portfolio management system that leverages LLMs and vector embeddings to provide intelligent portfolio analysis and management capabilities. The system uses OpenAI's GPT models for natural language understanding and Pinecone for efficient vector search of financial intents.

## Setup Instructions

1. **Environment Setup**
   ```bash
   # Clone the repository
   git clone [your-repo-url]
   cd Finantial-assistant-MPC

   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```
   Open `.env` and add your API keys:
   - Add your OpenAI API key as `OPENAI_API_KEY`
   - Add your Pinecone API key as `PINECONE_API_KEY`
   - Other variables are pre-configured but can be modified if needed

3. **Initialize the Application**
   ```bash
   # Run the setup script to create database and initialize indexes
   python app.py setup
   ```
   This will:
   - Create the SQLite database
   - Initialize Pinecone indexes
   - Set up necessary data structures

## Running the Application

```bash
python app.py
```

## Features

- Natural language processing for portfolio queries
- Multi-portfolio management
- Real-time financial data analysis
- Vector-based intent matching
- Secure data storage with SQLite

## Requirements

- Python 3.8+
- OpenAI API key
- Pinecone API key
- Internet connection for real-time financial data

## Security Note

The `.env` file contains sensitive API keys and is automatically ignored by Git. Never commit your actual API keys to version control. 