resource "google_service_account" "default" {
  account_id   = "service-account-id"
  display_name = "Service Account"
}

resource "google_container_cluster" "primary" {
  name     = "my-gke-cluster"
  location = "us-central1"

  private_cluster_config {
    enable_private_nodes = true
  }
  ip_allocation_policy = "yes"
  network_policy {
    enabled = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "0.0.0.0/0"
      display_name = "external"
    }
  }
  resource_labels = {
    "env" = "staging"
  }
}
