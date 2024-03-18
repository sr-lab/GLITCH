resource "google_compute_ssl_policy" "bad_example" {
}

resource "google_compute_ssl_policy" "bad_example2" {
  min_tls_version = "TLS_1_1"
}

resource "google_compute_ssl_policy" "good_example" {
  min_tls_version = "TLS_1_2"
}
