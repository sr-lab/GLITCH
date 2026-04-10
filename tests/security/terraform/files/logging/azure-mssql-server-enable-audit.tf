resource "azurerm_mssql_server" "bad_example" {
  public_network_access_enabled = false
}

resource "azurerm_mssql_server" "good_example" {
  public_network_access_enabled = false
}

resource "azurerm_mssql_server_extended_auditing_policy" "example" {
  server_id                               = azurerm_mssql_server.good_example.id
  storage_endpoint                        = azurerm_storage_account.example.primary_blob_endpoint
  storage_account_access_key              = azurerm_storage_account.example.primary_access_key
  storage_account_access_key_is_secondary = false
  retention_in_days                       = 90
}

