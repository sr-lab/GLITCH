resource "aws_secretsmanager_secret" "bad_example" {
  name       = "lambda_password"
}

resource "aws_secretsmanager_secret" "bad_example2" {
  name       = "lambda_password"
  kms_key_id = ""
}

resource "aws_secretsmanager_secret" "good_example" {
  name       = "lambda_password"
  kms_key_id = aws_kms_key.secrets.arn
}
