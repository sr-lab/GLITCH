resource "azurerm_kubernetes_cluster" "bad_example" {
  network_profile {
    network_policy = "azure"
  }
  api_server_access_profile {
    authorized_ip_ranges = ["198.51.100.0/24"]
  }
}

resource "azurerm_kubernetes_cluster" "bad_example2" {
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = ""
    }
  }

  network_profile {
    network_policy = "azure"
  }
  api_server_access_profile {
    authorized_ip_ranges = ["198.51.100.0/24"]
  }
}

resource "azurerm_kubernetes_cluster" "good_example" {
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "workspaceResourceId"
    }
  }

  network_profile {
    network_policy = "azure"
  }
  api_server_access_profile {
    authorized_ip_ranges = ["198.51.100.0/24"]
  }
}
