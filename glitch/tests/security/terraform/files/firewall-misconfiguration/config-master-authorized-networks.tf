resource "google_container_cluster" "bad_example" {
  private_cluster_config {
    enable_private_nodes = true
  }
  ip_allocation_policy {}
  network_policy {
    enabled = true
  }
  enable_legacy_abac = false
  resource_labels = {
    "env" = "staging"
  }
}

resource "google_container_cluster" "good_example" {
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "0.1.0.0/24"
    }
  }

  private_cluster_config {
    enable_private_nodes = true
  }
  ip_allocation_policy {}
  network_policy {
    enabled = true
  }
  enable_legacy_abac = false
  resource_labels = {
    "env" = "staging"
  }
}
