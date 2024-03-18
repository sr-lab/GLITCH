resource "azurerm_storage_account" "bad_example" {
  network_rules {
    default_action = "deny"
  }
}

resource "azurerm_storage_account_customer_managed_key" "bad_example" {
  storage_account_id = azurerm_storage_account.bad_example.id
}


resource "azurerm_storage_account" "bad_example2" {
  queue_properties  {
    logging {
      delete                = false
      read                  = false
      write                 = false
    }
  }
  
  network_rules {
    default_action = "deny"
  }
}

resource "azurerm_storage_account_customer_managed_key" "bad_example2" {
  storage_account_id = azurerm_storage_account.bad_example2.id
}

resource "azurerm_storage_account" "good_example" {
  queue_properties  {
    logging {
      delete                = true
      read                  = true
      write                 = true
    }
  }

  network_rules {
    default_action = "deny"
  }
}

resource "azurerm_storage_account_customer_managed_key" "good_example" {
  storage_account_id = azurerm_storage_account.good_example.id
}

