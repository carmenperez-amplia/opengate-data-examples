ALARM_FILTERS = {
    "all_alarms": {},
    "critical_alarms": {
        "filter": {
            "eq": { "alarm.severity": "CRITICAL" }
        }
    },
    "open_alarms": {
        "filter": {
            "eq": { "alarm.status": "OPEN" }
        }
    }
}

ENTITY_FILTERS = {
    "active_devices": {
        "filter": { "eq": { "resourceType": "entity.device" } },
        "select": [
            {
                "name": "provision.device.identifier",
                "fields": [
                    { "field": "value", "alias": "id" },
                    { "field": "date", "alias": "date" }
                ]
            }
        ],
        "limit": { "size": 25, "start": 1 }
    },
    "all_devices": {
        "filter": { "eq": { "resourceType": "entity.device" } },
        "select": [
            { "name": "provision.device.identifier", "fields": [{ "field": "value", "alias": "ID" }] },
            { "name": "provision.device.administrativeState", "fields": [{ "field": "value", "alias": "STATE" }] },
            { "name": "provision.device.communicationModules[].mobile.imei", "fields": [{ "field": "value", "alias": "IMEI" }] }
        ],
        "limit": { "size": 25, "start": 1 }
    },
    "device_status": {
        "filter": { "eq": { "resourceType": "entity.device" } },
        "select": [
            { "name": "provision.device.identifier", "fields": [{ "field": "value", "alias": "ID" }] },
            { "name": "provision.device.name", "fields": [{ "field": "value", "alias": "NAME" }] },
            { "name": "provision.device.communicationModules[].subscription.administrativeState", "fields": [{ "field": "value", "alias": "SIM_ADMIN_STATE" }] },
            { "name": "provision.device.communicationModules[].subscription.address", "fields": [{ "field": "value", "alias": "IP_ADDRESS/APN" }] },
            { "name": "device.communicationModules[].subscription.presence.unifiedPresence", "fields": [{ "field": "value", "alias": "UNIFIED_PRESENCE" }] },
            { "name": "provision.device.model", "fields": [{ "field": "value", "alias": "MODEL" }] },
            { "name": "enel.device.command.zkeepalive", "fields": [{ "field": "value", "alias": "ZKEEPALIVE_STATE" }] },
            { "name": "device.communicationModules[].subscription.presence.ipRtt", "fields": [{ "field": "value", "alias": "IP_RTT" }] },
            { "name": "device.communicationModules[].operationalStatus", "fields": [{ "field": "value", "alias": "OPERATIONAL_STATUS" }] },
            { "name": "provision.device.administrativeState", "fields": [{ "field": "value", "alias": "DEVICE_ADMIN_STATE" }] }
        ],
        "limit": { "size": 25, "start": 1 }
    }
}
