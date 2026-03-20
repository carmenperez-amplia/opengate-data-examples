from opengate_data import OpenGateClient
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path so we can import filters.py
sys.path.append(str(Path(__file__).parent.parent / "src"))
from opengate_alarms.filters import ENTITY_FILTERS

# Load environment variables from .env file
load_dotenv()

def search_active_devices():
    """
    Example of how to search for entities using the opengate-data library.
    Reuses the filter definition from src/opengate_alarms/filters.py.
    """
    # Configuration
    # Note: opengate-data client expects the base URL (without /north/v80)
    base_url = os.getenv("OPENGATE_BASE_URL", "https://api.opengate.es")
    if "/north/v80" in base_url:
        base_url = base_url.replace("/north/v80", "")
    
    api_key = os.getenv("OPENGATE_API_KEY")
    
    # Initialize the client
    client = OpenGateClient(api_key=api_key, url=base_url)
    
    # Load search criteria from filters.py
    search_config = ENTITY_FILTERS.get("active_devices", {})
    
    print(f"Searching entities in {base_url}...")
    
    # Create the search builder
    builder = client.new_entities_search_builder()
    
    if "filter" in search_config:
        builder.with_filter(search_config["filter"])
    
    if "select" in search_config:
        builder.with_select(search_config["select"])
        
    if "limit" in search_config:
        limit = search_config["limit"]
        builder.with_limit(limit.get("size", 25), limit.get("start", 1))
    
    # Execute the search and get results as a dict (JSON string)
    try:
        results_raw = builder.with_format("dict").build_execute()
        
        # opengate-data returns a JSON string that needs parsing
        data = json.loads(results_raw)
        
        # The key in the response matches the resource type or is 'entities'
        entities = []
        for key in ["entities", "devices", "alarms"]:
            if key in data and isinstance(data[key], list):
                entities = data[key]
                break
        
        print(f"\nFound {len(entities)} entities:")
        for entity in entities:
            # Print a snippet of the entity based on common fields or ID
            # In a real scenario, you'd extract fields based on your 'select' clause
            print(f"- {json.dumps(entity)}")
            
    except Exception as e:
        print(f"An error occurred during search: {e}")

if __name__ == "__main__":
    search_active_devices()
