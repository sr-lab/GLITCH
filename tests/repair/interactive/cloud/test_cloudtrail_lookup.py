import json
import unittest
from typing import Any, Dict, List

from glitch.repair.interactive.cloud.cloudtrail import CloudTrailLookupSource


class StubCloudTrailClient:
    def __init__(self, responses: List[Dict]) -> None:
        self.responses = responses
        self.calls: List[Dict[str, Any]] = []

    def lookup_events(self, **kwargs: Any) -> Dict:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class TestCloudTrailLookupSource(unittest.TestCase):
    def test_reads_all_pages(self) -> None:
        client = StubCloudTrailClient(
            [
                {
                    "Events": [
                        {
                            "CloudTrailEvent": json.dumps(
                                {
                                    "eventSource": "ec2.amazonaws.com",
                                    "eventName": "ModifyInstanceAttribute",
                                    "requestParameters": {"instanceId": "i-123"},
                                }
                            )
                        }
                    ],
                    "NextToken": "page-2",
                },
                {
                    "Events": [
                        {
                            "CloudTrailEvent": json.dumps(
                                {
                                    "eventSource": "s3.amazonaws.com",
                                    "eventName": "PutBucketAcl",
                                    "requestParameters": {"bucketName": "bucket-1"},
                                }
                            )
                        }
                    ]
                },
            ]
        )

        events = CloudTrailLookupSource(client=client).lookup(
            page_size=10, StartTime="start", EndTime="end"
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(client.calls[0]["MaxResults"], 10)
        self.assertEqual(client.calls[0]["StartTime"], "start")
        self.assertEqual(client.calls[1]["NextToken"], "page-2")
        self.assertEqual(client.calls[1]["EndTime"], "end")


if __name__ == "__main__":
    unittest.main()
