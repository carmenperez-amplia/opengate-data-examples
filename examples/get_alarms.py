from opengate_data import OpenGateClient
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path so we can import filters.py
sys.path.append(str(Path(__file__).parent.parent / "src"))
from opengate_alarms.filters import ALARM_FILTERS

# Load environment variables from .env file
load_dotenv()

def get_open_alarms():
    """
    Example of how to retrieve alarms using opengate-data library.
    Reuses the filter definition from src/opengate_alarms/filters.py.
    """
    # Configuration
    base_url = os.getenv("OPENGATE_BASE_URL", "https://api.opengate.es")
    # opengate-data appends paths automatically
    if "/north/v80" in base_url:
        base_url = base_url.replace("/north/v80", "")
    
    api_key = os.getenv("OPENGATE_API_KEY")
    
    # Load filter from the project's filters.py module
    payload = ALARM_FILTERS.get("open_alarms", {})
    
    print(f"Querying {base_url} via opengate-data...")
    print(f"Using filter: {json.dumps(payload, indent=2)}")
    
    client = OpenGateClient(api_key=api_key, url=base_url)
    builder = client.new_alarm_search_builder()
    
    if "filter" in payload:
        builder.with_filter(payload["filter"])
    if "limit" in payload:
        limit = payload["limit"]
        builder.with_limit(limit.get("size", 50), limit.get("start", 1))
        
    builder.with_format("dict")
        
    try:
        results_raw = builder.build_execute()
        data = json.loads(results_raw) if isinstance(results_raw, str) else results_raw
        
        # The response is usually a list of alarms or a dict containing them
        alarms = data if isinstance(data, list) else data.get("alarms", [])
        
        print(f"\nFound {len(alarms)} open alarms:")
        for alarm in alarms:
            # Handle both direct field access and 'alarm.' prefixed fields
            alarm_id = alarm.get("identifier") or alarm.get("alarm.identifier", "N/A")
            entity_id = alarm.get("entityIdentifier") or alarm.get("alarm.entityIdentifier", "N/A")
            name = alarm.get("name") or alarm.get("alarm.name", "N/A")
            severity = alarm.get("severity") or alarm.get("alarm.severity", "N/A")
            
            print(f"- [{severity}] {name} (ID: {alarm_id}, Entity: {entity_id})")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    get_open_alarms()
