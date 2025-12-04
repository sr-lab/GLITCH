resource "azurerm_kubernetes_cluster" "bad_example" {
  role_based_access_control_enabled = true
  api_server_access_profile {
    authorized_ip_ranges = ["1.1.1.1"]
  }
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "something"
    }
  }
}

resource "azurerm_kubernetes_cluster" "bad_example2" {
  network_profile {
    network_policy = ""
  }

  role_based_access_control_enabled = true
  api_server_access_profile {
    authorized_ip_ranges = ["1.1.1.1"]
  }
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "something"
    }
  }
}

resource "azurerm_kubernetes_cluster" "good_example" {
  network_profile {
    network_policy = "calico"
  }

  role_based_access_control_enabled = true
  api_server_access_profile {
    authorized_ip_ranges = ["1.1.1.1"]
  }
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "something"
    }
  }
}

resource "azurerm_kubernetes_cluster" "good_example2" {
  network_profile {
    network_policy = "azure"
  }

  role_based_access_control_enabled = true
  api_server_access_profile {
    authorized_ip_ranges = ["1.1.1.1"]
  }
  addon_profile {
    oms_agent {
      log_analytics_workspace_id = "something"
    }
  }
}
