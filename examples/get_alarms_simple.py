from opengate_data import OpenGateClient
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_open_alarms_simple():
    """
    SIMPLE EXAMPLE: Using opengate-data library.
    Get all open alarms from the OpenGate platform.
    """
    # 1. Configuration from .env
    base_url = os.getenv("OPENGATE_BASE_URL", "https://api.opengate.es")
    if "/north/v80" in base_url:
        base_url = base_url.replace("/north/v80", "")
    
    api_key = os.getenv("OPENGATE_API_KEY")
    
    print(f"--- Simple Alarm Search ---")
    print(f"URL: {base_url}")
    
    # 2. Initialize the client
    client = OpenGateClient(api_key=api_key, url=base_url)
    
    try:
        builder = client.new_alarm_search_builder()
        
        # 3. Build the search with embedded criteria
        results_raw = (builder
            .with_filter({"eq": {"alarm.status": "OPEN"}})
            .with_limit(10, 1)
            .with_format("dict")
            .build_execute()
        )
        
        data = json.loads(results_raw) if isinstance(results_raw, str) else results_raw
        alarms = data if isinstance(data, list) else data.get("alarms", [])
        
        print(f"Found {len(alarms)} alarms.\n")
        for alarm in alarms:
            name = alarm.get("alarm.name", alarm.get("name", "N/A"))
            severity = alarm.get("alarm.severity", alarm.get("severity", "N/A"))
            print(f"- [{severity}] {name}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_open_alarms_simple()
