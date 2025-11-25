resource "aws_iam_account_password_policy" "bad_example" {
  require_numbers = true
  require_lowercase_characters = true
  minimum_password_length = 14
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}

resource "aws_iam_account_password_policy" "bad_example2" {
  password_reuse_prevention = 1

  require_numbers = true
  require_lowercase_characters = true
  minimum_password_length = 14
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}

resource "aws_iam_account_password_policy" "good_example" {
  password_reuse_prevention = 5

  require_numbers = true
  require_lowercase_characters = true
  minimum_password_length = 14
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}
