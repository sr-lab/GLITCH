resource "google_kms_crypto_key" "bad_example" {
  name            = "crypto-key-example"
  key_ring        = google_kms_key_ring.keyring.id
}

resource "google_kms_crypto_key" "bad_example2" {
  name            = "crypto-key-example"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776001s"
}

resource "google_kms_crypto_key" "bad_example3" {
  name            = "crypto-key-example"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "something"
}

resource "google_kms_crypto_key" "good_example" {
  name            = "crypto-key-example"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s"
}
