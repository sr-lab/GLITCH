resource "google_bigquery_dataset" "dataset" {
  test  = "test ${var.value1}"
  test2 = "test ${"${var.value2}"}"
}