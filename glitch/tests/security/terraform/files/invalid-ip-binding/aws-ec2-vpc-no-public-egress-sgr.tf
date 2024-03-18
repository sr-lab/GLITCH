resource "aws_security_group" "bad_example" {
  description = "something"
  egress {
    description = "something"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "good_example" {
  description = "something"
  egress {
    description = "something"
    cidr_blocks = ["1.2.3.4/32"]
  }
}

resource "aws_security_group_rule" "bad_example" {
  description = "something"
  type = "egress"
  cidr_blocks = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "good_example" {
  description = "something"
  type = "egress"
  cidr_blocks = ["10.0.0.0/16"]
}