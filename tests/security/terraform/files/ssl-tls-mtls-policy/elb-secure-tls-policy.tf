resource "aws_alb_listener" "bad_example" {
  protocol = "HTTPS"
}

resource "aws_alb_listener" "bad_example" {
  ssl_policy = "ELBSecurityPolicy-TLS-1-1-2017-01"
  protocol = "HTTPS"
}

resource "aws_alb_listener" "good_example" {
  ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"
  protocol = "HTTPS"
}
