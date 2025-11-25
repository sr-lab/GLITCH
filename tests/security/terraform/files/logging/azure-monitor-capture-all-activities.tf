resource "azurerm_monitor_log_profile" "bad_example" {
  retention_policy {
    days    = 365
  }
}

resource "azurerm_monitor_log_profile" "bad_example2" {
  categories = ["Action", "Delete", "something"]
  retention_policy {
    days    = 365
  }
}

resource "azurerm_monitor_log_profile" "good_example" {
  categories = ["Action", "Delete", "Write"]
  retention_policy {
    days    = 365
  }
}

resource "azurerm_monitor_log_profile" "good_example2" {
  categories = ["Action", "Delete", "Write", "something"]
  retention_policy {
    days    = 365
  }
}
