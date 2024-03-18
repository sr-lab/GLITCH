resource "google_storage_bucket_iam_member" "bad_example" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.admin"
  member = "allUsers"
}

resource "google_storage_bucket_iam_member" "bad_example2" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.admin"
  member = "allAuthenticatedUsers"
}

resource "google_storage_bucket_iam_member" "good_example" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.admin"
  member = "joe@example.com"
}

resource "google_storage_bucket_iam_binding" "bad_example3" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.admin"
  members = ["allAuthenticatedUsers", "joe@example.com"]
}

resource "google_storage_bucket_iam_binding" "good_example2" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.admin"
  members = ["joe@example.com"]
}
