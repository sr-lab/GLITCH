resource "google_container_cluster" "bad_example" {
  ip_allocation_policy {}
  private_cluster_config {
    enable_private_nodes = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "1.1.1.1"
    }
  }
  enable_legacy_abac = false
  resource_labels = {
    "env" = "staging"
  }
}

resource "google_container_cluster" "bad_example2" {
  network_policy {
    enabled = false
  }

  ip_allocation_policy {}
  private_cluster_config {
    enable_private_nodes = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "1.1.1.1"
    }
  }
  enable_legacy_abac = false
  resource_labels = {
    "env" = "staging"
  }
}

resource "google_container_cluster" "good_example" {
  network_policy {
    enabled = true
  }

  ip_allocation_policy {}
  private_cluster_config {
    enable_private_nodes = true
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block = "1.1.1.1"
    }
  }
  enable_legacy_abac = false
  resource_labels = {
    "env" = "staging"
  }
}
