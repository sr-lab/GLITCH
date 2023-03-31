resource "aws_launch_configuration" "bad_example" {
  associate_public_ip_address = true

  ebs_block_device {
    encrypted = true
  }
  root_block_device {
    encrypted = true
  }
}

resource "aws_launch_configuration" "good_example" {
  associate_public_ip_address = false

  ebs_block_device {
    encrypted = true
  }
  root_block_device {
    encrypted = true
  }
}
