resource "aws_iam_account_password_policy" "bad_example" {
  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}

resource "aws_iam_account_password_policy" "bad_example2" {
  minimum_password_length = 10
  
  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}

resource "aws_iam_account_password_policy" "good_example" {
  minimum_password_length = 14

  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}

resource "aws_iam_account_password_policy" "good_example2" {
  minimum_password_length = 20

  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  max_password_age = 90
}
