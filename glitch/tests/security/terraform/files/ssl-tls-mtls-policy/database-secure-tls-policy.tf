resource "azurerm_mssql_server" "bad_example" {
  minimum_tls_version          = "1.1"
  public_network_access_enabled = false
}

resource "azurerm_mssql_server_extended_auditing_policy" "bad_example" {
  server_id = azurerm_mssql_server.bad_example.id
}

resource "azurerm_mssql_server" "good_example" {
  minimum_tls_version          = "1.2"
  public_network_access_enabled = false
}

resource "azurerm_mssql_server_extended_auditing_policy" "good_example" {
  server_id = azurerm_mssql_server.good_example.id
}

resource "azurerm_postgresql_server" "bad_example" {
  public_network_access_enabled    = false
  ssl_enforcement_enabled          = true
  ssl_minimal_tls_version_enforced = "TLS1_1"
}

resource "azurerm_postgresql_server" "good_example" {
  public_network_access_enabled    = false
  ssl_enforcement_enabled          = true
  ssl_minimal_tls_version_enforced = "TLS1_2"
}
