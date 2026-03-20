import pytest
from unittest.mock import patch, MagicMock
from opengate_alarms.client import OpenGateAlarmClient
from opengate_alarms.models import Alarm, SearchRequest
from datetime import datetime

@pytest.mark.asyncio
async def test_query_alarms_mock():
    client = OpenGateAlarmClient(api_key="fake-key")
    
    mock_response = [
        {
            "identifier": "AL-001",
            "entityIdentifier": "DEV-01",
            "name": "Test Alarm",
            "severity": "CRITICAL",
            "status": "OPEN",
            "openingDate": "2023-10-27T10:00:00Z"
        }
    ]

    with patch('opengate_data.OpenGateClient.new_alarm_search_builder') as mock_builder_func:
        mock_builder = MagicMock()
        mock_builder_func.return_value = mock_builder
        mock_builder.build_execute.return_value = mock_response
        
        # Chained methods should return mock_builder
        mock_builder.with_filter.return_value = mock_builder
        mock_builder.with_limit.return_value = mock_builder
        mock_builder.with_format.return_value = mock_builder
        
        alarms = await client.query_alarms()
        
        assert len(alarms) == 1
        assert alarms[0].id == "AL-001"
        assert alarms[0].severity == "CRITICAL"

@pytest.mark.asyncio
async def test_get_summary_mock():
    client = OpenGateAlarmClient(api_key="fake-key")
    
    mock_response = {
        "summary": {
            "date": "2023-10-27T10:00:00Z",
            "count": 1,
            "summaryGroup": [
                {
                    "severity": {
                        "count": 1,
                        "list": [{"count": 1, "name": "CRITICAL"}]
                    }
                }
            ]
        }
    }

    with patch('opengate_data.OpenGateClient.new_alarm_search_builder') as mock_builder_func:
        mock_builder = MagicMock()
        mock_builder_func.return_value = mock_builder
        mock_builder.build_execute.return_value = mock_response
        
        # Chained methods
        mock_builder.with_summary.return_value = mock_builder
        mock_builder.with_filter.return_value = mock_builder
        mock_builder.with_format.return_value = mock_builder
        
        summary = await client.get_summary()
        
        assert summary.count == 1
        assert len(summary.summary_group) == 1
