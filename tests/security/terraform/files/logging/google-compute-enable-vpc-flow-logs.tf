resource "google_compute_subnetwork" "bad_example" {
}

resource "google_compute_subnetwork" "good_example" {
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}
