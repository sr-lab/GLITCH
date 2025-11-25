resource "aws_instance" "example" {
  user_data     = <<EOF
    #!/bin/bash
    sudo apt-get update
    sudo apt-get install -y apache2
    sudo systemctl start apache2
  EOF
}