resource "google_bigquery_dataset" "dataset" {
  access {
    user_by_email = google_service_account.bqowner.email
  }
  test  = "${var.value1}"
}

resource "google_service_account" "bqowner" {
  account_id = "bqowner"
  email = "email.com"
}