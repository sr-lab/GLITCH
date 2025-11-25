resource "aws_iam_account_password_policy" "bad_example" {
  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  minimum_password_length = 14
}

resource "aws_iam_account_password_policy" "bad_example2" {
  max_password_age = 91

  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  minimum_password_length = 14
}

resource "aws_iam_account_password_policy" "good_example" {
  max_password_age = 90
  
  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  require_symbols = true
  minimum_password_length = 14
}

resource "aws_iam_account_password_policy" "good_example2" {
  password_reuse_prevention = 5
  require_numbers = true
  require_lowercase_characters = true
  max_password_age = 10
  require_uppercase_characters = true
  require_symbols = true
  minimum_password_length = 14
}
