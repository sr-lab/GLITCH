resource "aws_security_group" "bad_example" {
}

resource "aws_security_group" "bad_example2" {
  description = ""
}

resource "aws_security_group" "good_example" {
  description = "description"
}
