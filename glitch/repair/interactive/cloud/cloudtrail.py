"""Identify changed resources from CloudTrail events."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
import json


@dataclass
class CloudTrailEvent:
    event_name: str
    event_source: str
    request_parameters: Dict
    response_elements: Optional[Dict]
    resources: List[Dict] = field(default_factory=list)
    event_time: str = ""
    user_agent: Optional[str] = None


@dataclass
class ChangedResource:
    """A changed resource, identified by type and physical identifier."""

    type_name: str
    identifier: str


class CloudTrailChangeDetector:
    """Maps supported mutating events to changed resources."""

    _EVENTS: Dict[str, Dict[str, str]] = {
        "ec2.amazonaws.com": {
            "ModifyInstanceAttribute": "instanceId",
        },
    }

    _TYPE_NAMES: Dict[str, str] = {
        "ec2.amazonaws.com": "AWS::EC2::Instance",
    }

    def detect(self, events: List[CloudTrailEvent]) -> List[ChangedResource]:
        changed: List[ChangedResource] = []
        for event in events:
            event_table = self._EVENTS.get(event.event_source)
            if event_table is None:
                continue
            identifier_key = event_table.get(event.event_name)
            if identifier_key is None:
                continue
            identifier = event.request_parameters.get(identifier_key)
            if identifier:
                changed.append(
                    ChangedResource(self._TYPE_NAMES[event.event_source], identifier)
                )
        return changed


def parse_events(data: dict) -> List[CloudTrailEvent]:
    """Parse CloudTrail JSON (the usual ``{"Records": [...]}`` envelope)."""
    records = data.get("Records", [data])
    events: List[CloudTrailEvent] = []
    for record in records:
        events.append(
            CloudTrailEvent(
                event_name=record.get("eventName", ""),
                event_source=record.get("eventSource", ""),
                request_parameters=record.get("requestParameters") or {},
                response_elements=record.get("responseElements"),
                resources=record.get("resources") or [],
                event_time=record.get("eventTime", ""),
                user_agent=record.get("userAgent"),
            )
        )
    return events


def parse_events_file(path: str) -> List[CloudTrailEvent]:
    with open(path) as f:
        return parse_events(json.load(f))


class CloudTrailApi(Protocol):
    def lookup_events(self, **kwargs: Any) -> Dict:
        ...


class CloudTrailLookupSource:
    """Fetch all matching CloudTrail pages using boto3."""

    def __init__(
        self, region_name: str = "us-east-1", client: Optional[CloudTrailApi] = None
    ) -> None:
        if client is None:
            import boto3

            client = boto3.client("cloudtrail", region_name=region_name)
        self._client = client

    def lookup(self, page_size: int = 50, **filters: Any) -> List[CloudTrailEvent]:
        events: List[CloudTrailEvent] = []
        next_token: Optional[str] = None

        while True:
            request = {"MaxResults": page_size, **filters}
            if next_token is not None:
                request["NextToken"] = next_token

            response = self._client.lookup_events(**request)
            for record in response.get("Events", []):
                detail = record.get("CloudTrailEvent")
                if detail:
                    events.extend(parse_events(json.loads(detail)))

            next_token = response.get("NextToken")
            if next_token is None:
                return events
