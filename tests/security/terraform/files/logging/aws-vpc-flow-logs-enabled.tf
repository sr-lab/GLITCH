resource "aws_flow_log" "good_example" {
  iam_role_arn    = "arn"
  log_destination = "log"
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.good_example.id
}

resource "aws_vpc" "good_example" {
}

resource "aws_vpc" "bad_example" {
}