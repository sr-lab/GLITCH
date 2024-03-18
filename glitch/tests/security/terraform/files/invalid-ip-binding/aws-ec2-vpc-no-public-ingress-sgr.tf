resource "aws_security_group_rule" "bad_example" {
  description = "something"
  type = "ingress"
  cidr_blocks = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "good_example" {
  description = "something"
  type = "ingress"
  cidr_blocks = ["10.0.0.0/16"]
}

resource "aws_security_group" "bad_example" {
  description = "something"
  ingress {
    description = "something"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "good_example" {
  description = "something"
  ingress {
    description = "something"
    cidr_blocks = ["1.2.3.4/32"]
  }
}
