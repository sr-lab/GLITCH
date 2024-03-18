resource "azurerm_key_vault" "bad_example" {
  enabled_for_disk_encryption = true
  network_acls {
    default_action = "Deny"
    bypass = "AzureServices"
  }
}

resource "azurerm_key_vault" "bad_example2" {
  enabled_for_disk_encryption = true
  purge_protection_enabled    = false
  network_acls {
    default_action = "Deny"
    bypass = "AzureServices"
  }
}

resource "azurerm_key_vault" "good_example" {
  enabled_for_disk_encryption = true
  purge_protection_enabled    = true
  network_acls {
    default_action = "Deny"
    bypass = "AzureServices"
  }
}
