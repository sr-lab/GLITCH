resource "google_project_iam_binding" "bad_example" {
  members = ["user:test@example.com"]
}

resource "google_project_iam_member" "bad_example" {
  member = "user:test@example.com"
}

resource "google_project_iam_binding" "good_example" {
  members = ["group:test@example.com"]
}

resource "google_project_iam_member" "good_example" {
  member = "group:test@example.com"
}
