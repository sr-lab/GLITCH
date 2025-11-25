resource "azurerm_key_vault" "bad_example" {
  enabled_for_disk_encryption = true
  soft_delete_retention_days  = 7
  purge_protection_enabled    = true
}

resource "azurerm_key_vault" "bad_example2" {
  enabled_for_disk_encryption = true
  soft_delete_retention_days  = 7
  purge_protection_enabled    = true

  network_acls {
    default_action = "Allow"
    bypass = "AzureServices"
  }
}

resource "azurerm_key_vault" "good_example" {
  enabled_for_disk_encryption = true
  soft_delete_retention_days  = 7
  purge_protection_enabled    = true

  network_acls {
    default_action = "Deny"
    bypass = "AzureServices"
  }
}
