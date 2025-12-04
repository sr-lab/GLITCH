resource "google_compute_disk" "bad_example" {
}

resource "google_compute_disk" "bad_example2" {
  disk_encryption_key {
    kms_key_self_link = ""
  }
}

resource "google_compute_disk" "good_example" {
  disk_encryption_key {
    kms_key_self_link = "something"
  }
}
