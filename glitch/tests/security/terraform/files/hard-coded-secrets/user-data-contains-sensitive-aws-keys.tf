resource "aws_instance" "bad_example" {
  ebs_block_device {
    encrypted = true
  }
  root_block_device {
    encrypted = true
  }

  user_data = <<EOF
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-west-2 
EOF
}

resource "aws_instance" "good_example" {
  ebs_block_device {
    encrypted = true
  }
  root_block_device {
    encrypted = true
  }

  user_data = <<EOF
  export GREETING=hello
EOF
}
