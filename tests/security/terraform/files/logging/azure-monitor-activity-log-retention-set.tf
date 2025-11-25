resource "azurerm_monitor_log_profile" "bad_example" {
  categories = ["Action", "Delete", "Write"]
}

resource "azurerm_monitor_log_profile" "bad_example2" {
  retention_policy {
    enabled = true
    days    = 7
  }

  categories = ["Action", "Delete", "Write"]
}

resource "azurerm_monitor_log_profile" "good_example" {
  retention_policy {
    enabled = true
    days    = 365
  }

  categories = ["Action", "Delete", "Write"]
}
