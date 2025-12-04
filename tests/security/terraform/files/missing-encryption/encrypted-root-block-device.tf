resource "aws_launch_configuration" "bad_example" {
  ebs_block_device {
    encrypted = true
  }
}

resource "aws_launch_configuration" "bad_example2" {
  ebs_block_device {
    encrypted = true
  }

  root_block_device {
    encrypted = false
  }
}

resource "aws_instance" "bad_example3" {
  ebs_block_device {
    encrypted = true
  }

  root_block_device {
    encrypted = false
  }
}

resource "aws_instance" "bad_example4" {
  ebs_block_device {
  }

  root_block_device {
    encrypted = true
  }
}

resource "aws_launch_configuration" "good_example" {
  ebs_block_device {
    encrypted = true
  }
  
  root_block_device {
    encrypted = true
  }
}

resource "aws_instance" "good_example2" {
  root_block_device {
    encrypted = true
  }
}