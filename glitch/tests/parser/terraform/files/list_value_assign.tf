resource "google_service_account" "bqowner" {
  keys = ["value1", [1, {key2 = "value2"}], {key3 = "value3"}]
}
