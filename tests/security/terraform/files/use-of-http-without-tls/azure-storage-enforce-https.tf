resource "azurerm_storage_account" "bad_example" {
  enable_https_traffic_only = false

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

resource "azurerm_storage_account_customer_managed_key" "bad_example" {
  storage_account_id = azurerm_storage_account.bad_example.id
}

resource "azurerm_storage_account" "good_example" {
  enable_https_traffic_only = true

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