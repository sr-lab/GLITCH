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
  network_policy {
    enabled = true
  }
  enable_legacy_abac = false
}

resource "google_container_cluster" "bad_example2" {
  resource_labels = {
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
  network_policy {
    enabled = true
  }
  enable_legacy_abac = false
}

resource "google_container_cluster" "good_example" {
  resource_labels = {
    "env" = "staging"
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
  network_policy {
    enabled = true
  }
  enable_legacy_abac = false
}
