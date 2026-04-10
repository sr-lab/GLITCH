resource "google_project_iam_member" "bad_example" {
  project = "project-123"
  role    = "roles/whatever"
  member  = "123-compute@developer.gserviceaccount.comm"
}

resource "google_project_iam_member" "bad_example2" {
  project = "project-123"
  role    = "roles/whatever"
  member  = "123@appspot.gserviceaccount.com"
}

resource "google_project_iam_member" "good_example" {
  project = "project-123"
  role    = "roles/whatever"
  member  = "123@something.com"
}
