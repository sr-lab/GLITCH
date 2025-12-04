resource "cloudstack_instance" "bad_example" {
  user_data        = <<EOF
export DATABASE_PASSWORD=\"SomeSortOfPassword\"
EOF
}

resource "cloudstack_instance" "good_example" {
  user_data        = <<EOF
export GREETING="Hello there"
EOF
}

resource "aws_launch_configuration" "bad_example" {
  user_data     = <<EOF
export DATABASE_PASSWORD=\"SomeSortOfPassword\"
EOF

  ebs_block_device {
    encrypted = true
  }
  root_block_device {
    encrypted = true
  }
}

resource "aws_launch_configuration" "good_example" {
  user_data     = <<EOF
export GREETING="Hello there"
EOF

  ebs_block_device {
    encrypted = true
  }
  root_block_device {
    encrypted = true
  }
}
