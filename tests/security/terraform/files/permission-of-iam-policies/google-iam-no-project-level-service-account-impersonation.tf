resource "google_project_iam_binding" "bad_example" {
  project = "project-123"
  role    = "roles/iam.serviceAccountUser"
}

resource "google_project_iam_binding" "good_example" {
  project = "project-123"
  role    = "roles/nothingInParticular"
}
