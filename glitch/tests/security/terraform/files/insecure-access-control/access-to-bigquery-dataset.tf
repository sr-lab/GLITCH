resource "google_bigquery_dataset" "bad_example" {
  access {
    special_group = "allAuthenticatedUsers"
  }

  access {
    domain = "hashicorp.com"
  }
}

resource "google_bigquery_dataset" "bad_example" {
  access {
    special_group = "projectReaders"
  }

  access {
    domain = "hashicorp.com"
  }
}
