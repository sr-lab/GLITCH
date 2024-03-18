resource "aws_iam_group" "support" {
  name =  "support"
}

resource aws_iam_group_policy mfa {
  group = aws_iam_group.support.name
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Deny",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
          "Bool": {
              "aws:MultiFactorAuthPresent":    ["false"]
          }
      }
    }
  ]
}
EOF
}

resource "aws_iam_group" "support2" {
  name =  "support2"
}

resource aws_iam_group_policy mfa2 {
  group = aws_iam_group.support2.name
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Deny",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
          "Bool": {
              "aws:MultiFactorAuthPresent":    ["true"]
          }
      }
    }
  ]
}
EOF
}

resource "aws_iam_group" "support3" {
  name =  "support2"
}
