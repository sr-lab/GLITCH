resource "aws_alb" "bad_example" {
  internal = true
}

resource "aws_alb" "bad_example2" {
  internal = true
  drop_invalid_header_fields = false
}

resource "aws_alb" "good_example" {
  internal = true
  drop_invalid_header_fields = true
}
