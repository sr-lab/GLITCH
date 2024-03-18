resource "aws_subnet" "bad_example" {
  vpc_id                  = "vpc-123456"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "good_example" {
  vpc_id                  = "vpc-123456"
  map_public_ip_on_launch = false
}
