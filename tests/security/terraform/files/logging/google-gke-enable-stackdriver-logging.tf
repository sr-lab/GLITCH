resource "google_container_cluster" "bad_example" {
  logging_service = "logging.googleapis.com"

  private_cluster_config {
    enable_private_nodes = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "1.1.1.1"
    }
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
  private_cluster_config {
    enable_private_nodes = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "1.1.1.1"
    }
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

resource "google_container_cluster" "good_example2" {
  logging_service = "logging.googleapis.com/kubernetes"

  private_cluster_config {
    enable_private_nodes = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "1.1.1.1"
    }
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
