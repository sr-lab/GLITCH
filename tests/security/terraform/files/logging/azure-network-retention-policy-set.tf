resource "azurerm_network_watcher_flow_log" "bad_example" {
}

resource "azurerm_network_watcher_flow_log" "bad_example2" {
  retention_policy {
    enabled = true
    days = 6
  }
}

resource "azurerm_network_watcher_flow_log" "good_example" {
  retention_policy {
    enabled = true
    days = 90
  }
}
