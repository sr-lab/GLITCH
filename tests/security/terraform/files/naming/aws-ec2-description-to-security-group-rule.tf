resource "aws_security_group" "bad_example" {
  description = "description"
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
   }
}

resource "aws_security_group" "bad_example2" {
  description = "description"
  ingress {
    description = ""
    from_port   = 80
    to_port     = 80
    cidr_blocks = [aws_vpc.main.cidr_block]
    protocol    = "tcp"
   }
}

resource "aws_security_group" "good_example" {
  description = "description"
  ingress {
    description = "HTTP from VPC"
    to_port     = 80
    from_port   = 80
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
   }
}
