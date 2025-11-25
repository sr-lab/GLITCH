resource "azurerm_storage_account" "bad_example" {
  min_tls_version          = "TLS1_1"

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

resource "azurerm_storage_account" "good_example2" {
  min_tls_version          = "TLS1_2"

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

resource "azurerm_storage_account_customer_managed_key" "good_example2" {
  storage_account_id = azurerm_storage_account.good_example2.id
}
