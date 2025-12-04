resource "aws_alb_listener" "bad_example" {
  ssl_policy = "elbsecuritypolicy-tls-1-2-ext-2018-06"
}

resource "aws_alb_listener" "bad_example2" {
  protocol = "HTTP"
  ssl_policy = "elbsecuritypolicy-tls-1-2-ext-2018-06"
}

resource "aws_alb_listener" "good_example" {
  protocol = "HTTPS"
  ssl_policy = "elbsecuritypolicy-tls-1-2-ext-2018-06"
}
