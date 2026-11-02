import os
import unittest
from tempfile import NamedTemporaryFile
from typing import Dict

from glitch.parsers.cloudformation import CloudFormationParser
from glitch.tech import Tech
from glitch.repair.interactive.cloud.cloudtrail import parse_events
from glitch.repair.interactive.cloud.cloudcontrol import MockCloudControlClient
from glitch.repair.interactive.cloud.pipeline import run_cloud_repair


def _modify_instance(instance_id: str, attribute: str, value: str):
    return parse_events(
        {
            "Records": [
                {
                    "eventSource": "ec2.amazonaws.com",
                    "eventName": "ModifyInstanceAttribute",
                    "requestParameters": {
                        "instanceId": instance_id,
                        "attribute": attribute,
                        "value": value,
                    },
                    "eventTime": "2024-01-01T00:00:00Z",
                }
            ]
        }
    )


def _repair(template: str, events, resources: Dict[str, Dict]) -> str:
    f = NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False)
    f.write(template)
    f.flush()
    f.close()
    try:
        return run_cloud_repair(
            f.name,
            CloudFormationParser(),
            Tech.cloudformation,
            events,
            MockCloudControlClient(resources),
        )
    finally:
        os.unlink(f.name)


class TestEc2Drift(unittest.TestCase):
    def test_repairs_only_the_drifted_attribute(self) -> None:
        """Repairs InstanceType while preserving AvailabilityZone."""
        template = """\
AWSTemplateFormatVersion: "2010-09-09"
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t2.micro
      AvailabilityZone: us-east-1a
"""
        # The test uses a logical ID because physical-ID correlation is deferred.
        content = _repair(
            template,
            _modify_instance("MyInstance", "instanceType", "t2.large"),
            {
                "AWS::EC2::Instance:MyInstance": {
                    "TypeName": "AWS::EC2::Instance",
                    "Properties": {
                        "InstanceType": "t2.large",
                        "AvailabilityZone": "us-east-1a",
                    },
                }
            },
        )

        self.assertIn("InstanceType: t2.large", content)
        self.assertNotIn("t2.micro", content)
        self.assertIn("AvailabilityZone: us-east-1a", content)
        self.assertEqual(content.count("AvailabilityZone"), 1)

    def test_uses_cloud_control_state_not_cloudtrail_value(self) -> None:
        """CloudTrail identifies the resource, Cloud Control supplies its state."""
        template = """\
AWSTemplateFormatVersion: "2010-09-09"
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t2.micro
      AvailabilityZone: us-east-1a
"""
        content = _repair(
            template,
            _modify_instance("MyInstance", "instanceType", "t2.small"),
            {
                "AWS::EC2::Instance:MyInstance": {
                    "TypeName": "AWS::EC2::Instance",
                    "Properties": {
                        "InstanceType": "t2.large",
                        "AvailabilityZone": "us-east-1a",
                    },
                }
            },
        )

        self.assertIn("InstanceType: t2.large", content)
        self.assertNotIn("t2.small", content)

    def test_matching_live_state_leaves_template_unchanged(self) -> None:
        """A template already matching live state requires no edits."""
        template = """\
AWSTemplateFormatVersion: "2010-09-09"
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t2.large
      AvailabilityZone: us-east-1a
"""
        content = _repair(
            template,
            _modify_instance("MyInstance", "instanceType", "t2.large"),
            {
                "AWS::EC2::Instance:MyInstance": {
                    "TypeName": "AWS::EC2::Instance",
                    "Properties": {
                        "InstanceType": "t2.large",
                        "AvailabilityZone": "us-east-1a",
                    },
                }
            },
        )

        self.assertEqual(content, template)

    def test_repairs_through_parameter_reference(self) -> None:
        """Updates a referenced Parameter default and preserves the !Ref."""
        template = """\
AWSTemplateFormatVersion: "2010-09-09"
Parameters:
  InstanceTypeParam:
    Type: String
    Default: t2.micro
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceTypeParam
      AvailabilityZone: us-east-1a
"""
        content = _repair(
            template,
            _modify_instance("MyInstance", "instanceType", "t2.large"),
            {
                "AWS::EC2::Instance:MyInstance": {
                    "TypeName": "AWS::EC2::Instance",
                    "Properties": {
                        "InstanceType": "t2.large",
                        "AvailabilityZone": "us-east-1a",
                    },
                }
            },
        )

        self.assertIn("Default: t2.large", content)
        self.assertNotIn("t2.micro", content)
        self.assertIn("!Ref InstanceTypeParam", content)
        self.assertIn("AvailabilityZone: us-east-1a", content)


if __name__ == "__main__":
    unittest.main()
