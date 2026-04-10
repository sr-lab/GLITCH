resource "google_bigquery_dataset" "dataset" {
  test  = "test ${var.value1}"
  test2 = "test ${"${var.value2}"}"
  test3 = "filter('env', '${var.environment}') and filter('sfx_monitored', 'true')"
}