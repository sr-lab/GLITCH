resource "google_compute_disk" "good_example" {
  disk_encryption_key {
    raw_key = "b2ggbm8gdGhpcyBpcyBiYWQ="
    kms_key_self_link = google_kms_crypto_key.my_crypto_key.id
  }
}

resource "google_compute_disk" "good_example" {
  disk_encryption_key {
    kms_key_self_link = google_kms_crypto_key.my_crypto_key.id
  }
}
