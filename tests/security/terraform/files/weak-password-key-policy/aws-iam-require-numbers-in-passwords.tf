resource "aws_iam_account_password_policy" "bad_example" {
  password_reuse_prevention = 5
  require_symbols = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  max_password_age = 90
  minimum_password_length = 14
}

resource "aws_iam_account_password_policy" "bad_example2" {
  require_numbers = false

  password_reuse_prevention = 5
  require_symbols = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  max_password_age = 90
  minimum_password_length = 14
}

resource "aws_iam_account_password_policy" "good_example" {
  require_numbers = true
  
  password_reuse_prevention = 5
  require_symbols = true
  require_lowercase_characters = true
  require_uppercase_characters = true
  max_password_age = 90
  minimum_password_length = 14
}
