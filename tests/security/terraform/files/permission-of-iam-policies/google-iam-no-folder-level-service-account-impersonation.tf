resource "google_folder_iam_binding" "bad_example" {
  folder = "folder-123"
  role    = "roles/iam.serviceAccountUser"
}

resource "google_folder_iam_binding" "good_example" {
  folder = "folder-123"
  role    = "roles/nothingInParticular"
}
