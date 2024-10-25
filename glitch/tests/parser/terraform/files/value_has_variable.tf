resource "google_bigquery_dataset" "dataset" {
  test  = "test ${var.value1}"
}