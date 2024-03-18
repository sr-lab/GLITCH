resource "aws_lb" "bad_example" {
  drop_invalid_header_fields = true
}

resource "aws_lb" "bad_example2" {
  drop_invalid_header_fields = true
  internal = false
}

resource "aws_lb" "good_example" {
  drop_invalid_header_fields = true
  internal = true
}
