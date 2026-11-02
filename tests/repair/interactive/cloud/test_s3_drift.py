import os
import unittest
from tempfile import NamedTemporaryFile

from glitch.parsers.cloudformation import CloudFormationParser
from glitch.repair.interactive.cloud.cloudcontrol import MockCloudControlClient
from glitch.repair.interactive.cloud.cloudtrail import parse_events
from glitch.repair.interactive.cloud.pipeline import run_cloud_repair
from glitch.tech import Tech


class TestS3Drift(unittest.TestCase):
    def test_repairs_bucket_acl(self) -> None:
        template = """\
AWSTemplateFormatVersion: "2010-09-09"
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-drifted-bucket
      AccessControl: Private
"""
        events = parse_events(
            {
                "Records": [
                    {
                        "eventSource": "s3.amazonaws.com",
                        "eventName": "PutBucketAcl",
                        "requestParameters": {
                            "bucketName": "my-drifted-bucket",
                            "x-amz-acl": "public-read",
                        },
                    }
                ]
            }
        )
        cloud_control = MockCloudControlClient(
            {
                "AWS::S3::Bucket:my-drifted-bucket": {
                    "TypeName": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": "my-drifted-bucket",
                        "AccessControl": "PublicRead",
                    },
                }
            }
        )

        f = NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False)
        f.write(template)
        f.flush()
        f.close()
        try:
            content = run_cloud_repair(
                f.name,
                CloudFormationParser(),
                Tech.cloudformation,
                events,
                cloud_control,
            )
        finally:
            os.unlink(f.name)

        self.assertIn("AccessControl: PublicRead", content)
        self.assertNotIn("AccessControl: Private", content)


if __name__ == "__main__":
    unittest.main()
