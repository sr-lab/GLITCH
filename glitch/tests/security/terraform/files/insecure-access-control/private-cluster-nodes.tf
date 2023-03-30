resource "google_container_cluster" "bad_example" {
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
}

resource "google_container_cluster" "bad_example" {
  private_cluster_config {
    enable_private_nodes = false
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
}
