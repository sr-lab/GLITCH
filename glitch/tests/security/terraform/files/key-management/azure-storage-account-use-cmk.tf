resource "azurerm_storage_account" "storage_account_bad" {
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

resource "azurerm_storage_account" "storage_account_good_1" {
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

resource "azurerm_storage_account_customer_managed_key" "managed_key_good" {
  storage_account_id = azurerm_storage_account.storage_account_good_1.id
}
