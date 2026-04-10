resource "google_bigquery_dataset" "dataset" {
  labels = {
    env = "default"
  }
}