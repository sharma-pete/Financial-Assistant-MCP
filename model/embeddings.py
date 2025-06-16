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
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        self.index_name = PINECONE_INDEX
        self.setup_index()

    def setup_index(self):
        """Create Pinecone index if it doesn't exist."""
        try:
            if not self.pc.has_index(self.index_name):
                self.pc.create_index_for_model(
                    name=self.index_name,
                    cloud=PINECONE_CLOUD,
                    region=PINECONE_ENVIRONMENT,
                    embed={
                        "model": "llama-text-embed-v2",
                        "field_map": {"text": "text"}
                    }
                )
            
            self.index = self.pc.Index(self.index_name)
            
            stats = self.index.describe_index_stats()
            
        except Exception as e:
            raise

    def generate_vector_id(self, tool_name: str, example: str) -> str:
        """Generate a unique vector ID for an example query."""
        return f"{tool_name}:{hash(example)}"

    def derive_intent_category(self, tool_name: str) -> str:
        """Derive the intent category from tool name."""
        categories = {
            "get": "retrieval",
            "compare": "analysis",
            "calculate": "computation",
            "show": "display",
            "list": "enumeration"
        }
        for key, category in categories.items():
            if tool_name.startswith(key):
                return category
        return "general"

    def enrich_text_for_embedding(self, tool: Dict[str, Any], example: str, metadata: Dict[str, str]) -> str:
        """Create focused text for embedding that prioritizes query patterns."""
        query_pattern = example.strip().lower()
        
        action = tool["name"].replace("_", " ").strip()
        core_purpose = tool["description"].split(".")[0].strip()
        
        return f"{query_pattern} | {action} | {core_purpose}"

    def prepare_metadata(self, tool: Dict[str, Any]) -> Dict[str, str]:
        """Prepare metadata for a tool using only string values."""
        return {
            "tool_name": tool["name"],
            "description": tool.get("description", ""),
            "param_names": ",".join(tool.get("parameters", {}).get("properties", {}).keys()),
            "required_params": ",".join(tool.get("parameters", {}).get("required", [])),
            "action_type": tool["name"].split("_")[0]
        }

    def upload_intents(self, intent_map_path: str, batch_size: int = 90):
        """Upload intent embeddings to Pinecone with batching support."""
        try:
            with open(intent_map_path, 'r') as f:
                intent_map = json.load(f)
            
            try:
                stats = self.index.describe_index_stats()
                if 'intents' in stats.get('namespaces', {}):
                    self.delete_all_vectors()
            except Exception as e:
                pass
            
            records_to_upsert = []
            total_examples = 0
            
            for tool in intent_map:
                tool_name = tool["name"]
                metadata = self.prepare_metadata(tool)
                
                for example in tool.get("examples", []):
                    vector_id = self.generate_vector_id(tool_name, example)
                    
                    enriched_text = self.enrich_text_for_embedding(tool, example, metadata)
                    
                    record = {
                        "_id": vector_id,
                        "text": enriched_text,
                        "tool_name": tool_name,
                        "example": example,
                        "description": tool.get("description", ""),
                        "param_names": metadata["param_names"],
                        "required_params": metadata["required_params"]
                    }
                    
                    records_to_upsert.append(record)
                    total_examples += 1
                    
                    if len(records_to_upsert) >= batch_size:
                        self.index.upsert_records(
                            namespace="intents",
                            records=records_to_upsert
                        )
                        records_to_upsert = []
            
            if records_to_upsert:
                self.index.upsert_records(
                    namespace="intents",
                    records=records_to_upsert
                )
            
        except Exception as e:
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
        try:
            results = self.index.search_records(
                namespace="intents",
                query={
                    "inputs": {"text": query},
                    "top_k": top_k
                },
                fields=["tool_name", "description", "param_names", "required_params", "example"]
            )
            
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
            raise

    def delete_all_vectors(self):
        """Delete all vectors from the intents namespace."""
        try:
            self.index.delete(delete_all=True, namespace="intents")
        except Exception as e:
            if "Namespace not found" in str(e):
                pass
            else:
                raise

    def upload_sectors(self, sector_map_path: str, batch_size: int = 90):
        """
        Upload sector mappings to Pinecone with enhanced context.
        
        Args:
            sector_map_path: Path to the sector map JSON file
            batch_size: Number of vectors to upsert in each batch (max 96 for Pinecone)
        """
        try:
            with open(sector_map_path, 'r') as f:
                sector_map = json.load(f)
            
            records_to_upsert = []
            total_variations = 0
            
            for sector in sector_map["sectors"]:
                canonical = sector["canonical"]
                variations = sector["variations"]
                
                sector_context = f"""
Primary Sector: {canonical}
Alternative Names: {", ".join(variations)}
Industry Context: {canonical} sector including {", ".join(variations[:3])}
Common Usage: Companies and investments in {canonical} industry
"""
                
                vector_id = f"sector:{hash(canonical)}"
                records_to_upsert.append({
                    "_id": vector_id,
                    "text": sector_context,
                    "canonical": canonical,
                    "variations": ",".join(variations)
                })
                total_variations += 1
                
                if len(records_to_upsert) >= batch_size:
                    self.index.upsert_records(
                        namespace="sectors",
                        records=records_to_upsert
                    )
                    records_to_upsert = []
                
                for variation in variations:
                    variation_context = f"""
Variation: {variation}
Primary Sector: {canonical}
Related Terms: {", ".join([v for v in variations if v != variation][:3])}
Industry Context: Part of {canonical} sector
"""
                    vector_id = f"sector:{hash(variation)}"
                    records_to_upsert.append({
                        "_id": vector_id,
                        "text": variation_context,
                        "canonical": canonical,
                        "variations": ",".join(variations)
                    })
                    total_variations += 1
                    
                    if len(records_to_upsert) >= batch_size:
                        self.index.upsert_records(
                            namespace="sectors",
                            records=records_to_upsert
                        )
                        records_to_upsert = []
            
            if records_to_upsert:
                self.index.upsert_records(
                    namespace="sectors",
                    records=records_to_upsert
                )
            
        except Exception as e:
            raise

    def find_canonical_sector(self, query: str, threshold: float = 0.7) -> tuple[str, float]:
        """Find canonical sector name for a query with similarity score."""
        try:
            results = self.index.search_records(
                namespace="sectors",
                query={
                    "inputs": {"text": query},
                    "top_k": 3
                },
                fields=["canonical"]
            )
            
            if results['result']['hits']:
                for hit in results['result']['hits']:
                    pass
                
                hit = results['result']['hits'][0]
                return hit['fields']['canonical'], hit['_score']
            
            return query, 0.0
            
        except Exception as e:
            return query, 0.0

    def find_closest_sectors(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find closest matching sectors for a query."""
        try:
            results = self.index.search_records(
                namespace="sectors",
                query={
                    "inputs": {"text": query},
                    "top_k": top_k
                },
                fields=["canonical", "variations"]
            )
            
            matches = []
            if results['result']['hits']:
                for hit in results['result']['hits']:
                    matches.append({
                        "canonical": hit['fields']['canonical'],
                        "variations": hit['fields']['variations'].split(','),
                        "similarity": hit['_score']
                    })
            
            return matches
            
        except Exception as e:
            return []

