import json
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from config import (
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX
)

class IntentEmbeddings:
    def __init__(self):
        """Initialize Pinecone client."""
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Set up Pinecone index
        self.index_name = PINECONE_INDEX
        self.setup_index()

    def setup_index(self):
        """Create Pinecone index if it doesn't exist."""
        print("--------------------------------we are in setup_index--------------------------------")
        try:
            if not self.pc.has_index(self.index_name):
                # Create new index with integrated embeddings
                self.pc.create_index_for_model(
                    name=self.index_name,
                    cloud=PINECONE_CLOUD,
                    region=PINECONE_ENVIRONMENT,
                    embed={
                        "model": "llama-text-embed-v2",
                        "field_map": {"text": "text"}  # Map 'text' field in our records to 'text' in embedding
                    }
                )
                print(f"Created new Pinecone index: {self.index_name}")
            else:
                print(f"Using existing Pinecone index: {self.index_name}")

            # Get index instance
            self.index = self.pc.Index(self.index_name)
            
            # Print index stats
            stats = self.index.describe_index_stats()
            print(f"Index stats: {stats}")
            
        except Exception as e:
            print(f"Error setting up Pinecone index: {str(e)}")
            raise

    def generate_vector_id(self, tool_name: str, example: str) -> str:
        """Generate a unique vector ID for an example query."""
        return f"{tool_name}:{hash(example)}"

    def prepare_metadata(self, tool: Dict[str, Any]) -> Dict[str, str]:
        """Prepare metadata for a tool using only string values."""
        print("--------------------------------we are in prepare_metadata--------------------------------")
        # Convert parameters to a simplified string format
        params = tool.get("parameters", {})
        param_properties = params.get("properties", {})
        param_names = list(param_properties.keys())
        required_params = params.get("required", [])
        
        obj = {
            "tool_name": tool["name"],
            "description": tool.get("description", ""),
            "param_names": ",".join(param_names) if param_names else "",  # Convert list to comma-separated string
            "required_params": ",".join(required_params) if required_params else ""  # Convert list to comma-separated string
        }

        return obj

    def upload_intents(self, intent_map_path: str, batch_size: int = 100):
        """
        Upload intent embeddings to Pinecone with batching support.
        
        Args:
            intent_map_path: Path to the intent map JSON file
            batch_size: Number of vectors to upsert in each batch
        """
        print("--------------------------------we are in upload_intents--------------------------------")
        try:
            # Load intent map
            with open(intent_map_path, 'r') as f:
                intent_map = json.load(f)
            
            print(f"Loaded {len(intent_map)} tools from intent map")
            
            # Prepare records for upload
            records_to_upsert = []
            total_examples = 0
            
            for tool in intent_map:
                tool_name = tool["name"]
                metadata = self.prepare_metadata(tool)
                
                # Process each example query
                for example in tool.get("examples", []):
                    vector_id = self.generate_vector_id(tool_name, example)
                    
                    # Add example to metadata
                    example_metadata = metadata.copy()
                    example_metadata["example"] = example

                    # Create record with flattened metadata
                    record = {
                        "_id": vector_id,
                        "text": example,  # This matches our field_map in setup_index
                    }
                    # Add all metadata fields directly to the record
                    record.update({
                        "tool_name": example_metadata["tool_name"],
                        "description": example_metadata["description"],
                        "param_names": example_metadata["param_names"],
                        "required_params": example_metadata["required_params"],
                        "example": example_metadata["example"]
                    })
                    records_to_upsert.append(record)
                    total_examples += 1
                    
                    # Batch upload if we've reached batch_size
                    if len(records_to_upsert) >= batch_size:
                        self.index.upsert_records(
                            namespace="intents",
                            records=records_to_upsert
                        )
                        print(f"Uploaded batch of {len(records_to_upsert)} records")
                        records_to_upsert = []
            
            # Upload any remaining records
            if records_to_upsert:
                self.index.upsert_records(
                    namespace="intents",
                    records=records_to_upsert
                )
                print(f"Uploaded final batch of {len(records_to_upsert)} records")
            
            print(f"Successfully uploaded {total_examples} examples for {len(intent_map)} tools")
            
        except Exception as e:
            print(f"Error uploading intents: {str(e)}")
            raise

    def find_closest_intent(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find the closest matching intents for a given query.
        
        Args:
            query: The user's query
            top_k: Number of closest matches to return
            
        Returns:
            List of closest matching intents with their metadata
        """
        print("--------------------------------we are in find_closest_intent--------------------------------")
        try:
            # Query Pinecone with text directly using search_records
            results = self.index.search_records(
                namespace="intents",
                query={
                    "inputs": {"text": query},
                    "top_k": top_k
                },
                fields=["tool_name", "description", "param_names", "required_params", "example"]
            )
            
            # Process and return results
            matches = []
            for match in results['result']['hits']:
                matches.append({
                    "tool_name": match['fields']["tool_name"],
                    "description": match['fields']["description"],
                    "param_names": match['fields']["param_names"],
                    "required_params": match['fields']["required_params"],
                    "example": match['fields']["example"],
                    "similarity": match['_score']
                })
            
            return matches
            
        except Exception as e:
            print(f"Error finding closest intent: {str(e)}")
            raise

    def delete_all_vectors(self):
        """Delete all vectors from the index (useful for testing/reset)."""
        try:
            self.index.delete(delete_all=True, namespace="intents")
            print(f"Deleted all vectors from namespace 'intents' in index {self.index_name}")
        except Exception as e:
            print(f"Error deleting vectors: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    intent_embeddings = IntentEmbeddings()
    
    # Upload intents
    intent_embeddings.upload_intents("model/intent_map.json")
    
    # Test some queries
    test_queries = [
        "What's the current price of Apple stock?",
        "Show me my portfolio value",
        "Compare Tesla and Amazon performance",
        "What sectors do I have investments in?",
        "Give me an overview of my investments"
    ]
    
    print("\nTesting queries:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        matches = intent_embeddings.find_closest_intent(query)
        print("Top matches:")
        for match in matches:
            print(f"- {match['tool_name']} (similarity: {match['similarity']:.3f})")
            print(f"  Example: {match['example']}")
