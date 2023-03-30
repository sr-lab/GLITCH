resource "google_storage_bucket" "bad_example" {
}

resource "google_storage_bucket" "bad_example2" {
  uniform_bucket_level_access = false
}

resource "google_storage_bucket" "good_example" {
  uniform_bucket_level_access = true
}
