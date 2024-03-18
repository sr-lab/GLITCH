resource "aws_network_acl_rule" "bad_example" {
  protocol       = -1
}

resource "aws_network_acl_rule" "good_example" {
  protocol       = "tcp"
}
