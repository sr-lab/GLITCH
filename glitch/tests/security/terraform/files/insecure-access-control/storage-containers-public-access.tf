resource "azurerm_storage_account" "good_example" {
  queue_properties {
    logging {
      delete = true
      read = true
      write = true
    }
  }
  network_rules {
    default_action = "deny"
  }
}

resource "azurerm_storage_account_customer_managed_key" "good_example" {
  storage_account_id = azurerm_storage_account.good_example.id
}

resource "azurerm_log_analytics_storage_insights" "good_example" {
  storage_account_id  = azurerm_storage_account.good_example.id
  blob_container_names = ["something"]
}


resource "azurerm_storage_container" "bad_example" {
  storage_account_name   = azurerm_storage_account.good_example.name
  container_access_type = "blob"
}

resource "azurerm_storage_container" "good_example" {
  storage_account_name   = azurerm_storage_account.good_example.name
}

resource "azurerm_storage_container" "good_example2" {
  storage_account_name   = azurerm_storage_account.good_example.name
  container_access_type = "private"
}
