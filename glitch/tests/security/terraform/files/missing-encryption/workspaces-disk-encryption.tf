resource "aws_workspaces_workspace" "bad_example" {
}

resource "aws_workspaces_workspace" "bad_example2" {
  root_volume_encryption_enabled = true
}

resource "aws_workspaces_workspace" "bad_example3" {
  user_volume_encryption_enabled = true
}

resource "aws_workspaces_workspace" "bad_example4" {
  root_volume_encryption_enabled = false
  user_volume_encryption_enabled = false
}

resource "aws_workspaces_workspace" "good_example" {
  root_volume_encryption_enabled = true
  user_volume_encryption_enabled = true
}
