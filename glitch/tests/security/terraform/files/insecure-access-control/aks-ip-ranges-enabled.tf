resource "azurerm_kubernetes_cluster" "bad_example" {
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "something"
    }
  }
  network_profile {
    network_policy = "azure"
  }
}

resource "azurerm_kubernetes_cluster" "good_example" {
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "something"
    }
  }
  network_profile {
    network_policy = "azure"
  }
  api_server_access_profile {
    authorized_ip_ranges = ["198.51.100.0/24"]
  }
}
