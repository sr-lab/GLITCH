resource "aws_iam_user" "jim" {
  name = "jim"
}

resource "aws_iam_user_policy" "bad_example" {
  name = "test"
  user = aws_iam_user.jim.name
}

resource "aws_iam_group" "developers" {
  name = "developers"
  path = "/users/"
}

resource "aws_iam_group_membership" "devteam" {
  name = "developers-team"

  users = [
    aws_iam_user.jim.name,
  ]

  group = aws_iam_group.developers.name
}

resource "aws_iam_group_policy" "good_example" {
  name = "test"
  group = aws_iam_group.developers.name
}
