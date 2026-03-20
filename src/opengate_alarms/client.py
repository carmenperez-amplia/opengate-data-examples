import httpx
import os
import asyncio
from typing import List, Optional, Dict, Any
from .models import Alarm, AlarmSummary, SearchRequest
from dotenv import load_dotenv
from opengate_data import OpenGateClient

import logging
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("opengate_alarms.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("opengate_alarms.client")

class OpenGateAlarmClient:

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENGATE_API_KEY")
        # Use provided base_url, or env var, or default to production
        env_url = os.getenv("OPENGATE_BASE_URL")
        if env_url:
            # Ensure we append the path if it's just the host
            if not env_url.endswith("/north/v80"):
                env_url = env_url.rstrip("/") + "/north/v80"
            self.base_url = env_url
        else:
            self.base_url = base_url or "https://api.opengate.es/north/v80"
        
        self.verify_ssl = os.getenv("OPENGATE_VERIFY_SSL", "True").lower() == "true"
        
        # Initialize opengate-data client
        og_url = self.base_url.replace("/north/v80", "")
        self.og_client = OpenGateClient(api_key=self.api_key, url=og_url)
        
        self.headers = {
            "X-ApiKey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def query_alarms(self, search_request: Optional[SearchRequest] = None) -> List[Alarm]:
        if search_request is None:
            search_request = SearchRequest()

        builder = self.og_client.new_alarm_search_builder()
        payload = search_request.model_dump(by_alias=True, exclude_none=True)
        
        if payload.get("filter"):
            builder.with_filter(payload["filter"])
            
        limit = payload.get("limit", {})
        if limit:
            builder.with_limit(limit.get("size", 50), limit.get("start", 1))
            
        builder.with_format("dict")
        logger.info(f"Querying alarms via opengate-data - Payload: {payload}")
        
        try:
            results_raw = await asyncio.to_thread(builder.build_execute)
            if isinstance(results_raw, str):
                import json
                data = json.loads(results_raw)
            else:
                data = results_raw
            
            alarms_list = data if isinstance(data, list) else data.get("alarms", [])
            return [Alarm(**item) for item in alarms_list]
        except Exception as e:
            logger.error(f"API Error in query_alarms: {e}")
            raise

    async def get_summary(self, filter_data: Optional[Dict[str, Any]] = None) -> AlarmSummary:
        builder = self.og_client.new_alarm_search_builder()
        builder.with_summary()
        
        if filter_data:
            builder.with_filter(filter_data)
            
        builder.with_format("dict")
        
        try:
            results_raw = await asyncio.to_thread(builder.build_execute)
            if isinstance(results_raw, str):
                import json
                data = json.loads(results_raw)
            else:
                data = results_raw
                
            return AlarmSummary(**data["summary"])
        except Exception as e:
            logger.error(f"API Error in get_summary: {e}")
            raise

    async def change_state(self, action: str, alarm_ids: List[str], notes: Optional[str] = None) -> bool:
        url = f"{self.base_url}/alarms"
        payload = {
            "action": action, # ATTEND or CLOSE
            "alarms": alarm_ids,
            "notes": notes
        }
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            return response.status_code == 200

