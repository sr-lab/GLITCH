resource "google_container_cluster" "bad_example" {
  master_auth {
    client_certificate_config {
    issue_client_certificate = true
    }
  }

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
  resource_labels = {
    "env" = "staging"
  }
}

resource "google_container_cluster" "good_example" {
  master_auth {
  }

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
  resource_labels = {
    "env" = "staging"
  }
}

resource "google_container_cluster" "good_example2" {
  master_auth {
    client_certificate_config {
    issue_client_certificate = false
    }
  }

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
  resource_labels = {
    "env" = "staging"
  }
}