resource "azurerm_storage_account_network_rules" "bad_example" {
  ip_rules                   = ["127.0.0.1"]
  virtual_network_subnet_ids = [azurerm_subnet.test.id]
  bypass                     = ["Metrics"]
}

resource "azurerm_storage_account_network_rules" "bad_example2" {
  default_action             = "Allow"
  ip_rules                   = ["127.0.0.1"]
  virtual_network_subnet_ids = [azurerm_subnet.test.id]
  bypass                     = ["Metrics"]
}

resource "azurerm_storage_account_network_rules" "good_example" {
  default_action             = "Deny"
  ip_rules                   = ["127.0.0.1"]
  virtual_network_subnet_ids = [azurerm_subnet.test.id]
  bypass                     = ["Metrics"]
}

resource "azurerm_storage_account" "bad_example" {
  queue_properties {
    logging {
      delete = true
      read = true
      write = true
    }
  }
}

resource "azurerm_storage_account_customer_managed_key" "managed_key_good" {
  storage_account_id = azurerm_storage_account.bad_example.id
}

resource "azurerm_storage_account" "good_example" {
  network_rules {
    default_action = "Deny"
  }

  queue_properties {
    logging {
      delete = true
      read = true
      write = true
    }
  }
}

resource "azurerm_storage_account_customer_managed_key" "managed_key_good" {
  storage_account_id = azurerm_storage_account.good_example.id
}