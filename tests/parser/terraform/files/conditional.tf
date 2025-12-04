resource "google_service_account" "bqowner" {
  account_id = var.create_service_account ? "bqowner" : null
}