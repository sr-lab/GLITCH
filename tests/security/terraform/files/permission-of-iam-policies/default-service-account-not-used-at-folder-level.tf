resource "google_folder_iam_member" "bad_example" {
  folder = "folder-123"
  role    = "roles/whatever"
  member  = "123-compute@developer.gserviceaccount.comm"
}

resource "google_folder_iam_member" "bad_example2" {
  folder = "folder-123"
  role    = "roles/whatever"
  member  = "123@appspot.gserviceaccount.com"
}

resource "google_folder_iam_member" "good_example" {
  folder = "folder-123"
  role    = "roles/whatever"
  member  = "123@something.com"
}
