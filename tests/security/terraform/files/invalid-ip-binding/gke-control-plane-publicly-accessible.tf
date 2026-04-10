resource "google_container_cluster" "bad_example" {
  ip_allocation_policy {}
  network_policy {
    enabled = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "0.0.0.0/0"
      display_name = "external"
    }
  }
  private_cluster_config {
    enable_private_nodes = true
  }
  resource_labels = {
    "env" = "staging"
  }
}

resource "google_container_cluster" "good_example" {
  ip_allocation_policy {}
  network_policy {
    enabled = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "10.10.128.0/24"
      display_name = "internal"
    }
  }
  private_cluster_config {
    enable_private_nodes = true
  }
  resource_labels = {
    "env" = "staging"
  }
}
