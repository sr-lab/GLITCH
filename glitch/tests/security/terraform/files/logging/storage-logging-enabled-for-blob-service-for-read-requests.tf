resource "azurerm_storage_container" "bad_example" {
  storage_account_name   = azurerm_storage_account.bad_example.name
  container_access_type  = "private"
}

# -----------------------------------------------------------------------------

resource "azurerm_storage_account" "bad_example2" {
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

resource "azurerm_storage_account_customer_managed_key" "bad_example2" {
  storage_account_id = azurerm_storage_account.bad_example2.id
}

resource "azurerm_storage_container" "bad_example2" {
  storage_account_name   = azurerm_storage_account.bad_example2.name
  container_access_type  = "private"
}

# -----------------------------------------------------------------------------

resource "azurerm_storage_account" "bad_example3" {
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

resource "azurerm_storage_account_customer_managed_key" "bad_example3" {
  storage_account_id = azurerm_storage_account.bad_example3.id
}

resource "azurerm_log_analytics_storage_insights" "bad_example3" {
  storage_account_id  = azurerm_storage_account.bad_example3.id
}

resource "azurerm_storage_container" "bad_example3" {
  storage_account_name   = azurerm_storage_account.bad_example3.name
  container_access_type  = "private"
}

# -----------------------------------------------------------------------------

resource "azurerm_storage_account" "bad_example4" {
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

resource "azurerm_storage_account_customer_managed_key" "bad_example4" {
  storage_account_id = azurerm_storage_account.bad_example4.id
}

resource "azurerm_log_analytics_storage_insights" "bad_example4" {
  storage_account_id  = azurerm_storage_account.bad_example4.id
  blob_container_names = [""]
}

resource "azurerm_storage_container" "bad_example4" {
  storage_account_name   = azurerm_storage_account.bad_example4.name
  container_access_type  = "private"
}

# -----------------------------------------------------------------------------

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

resource "azurerm_log_analytics_storage_insights" "good_example" {
  storage_account_id  = azurerm_storage_account.good_example.id
  blob_container_names = ["something"]
}

resource "azurerm_storage_container" "good_example" {
  storage_account_name   = azurerm_storage_account.good_example.name
  container_access_type  = "private"
}
