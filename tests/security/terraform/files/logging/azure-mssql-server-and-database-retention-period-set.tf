resource "azurerm_mssql_database_extended_auditing_policy" "bad_example" {
  database_id                             = azurerm_mssql_database.example.id
  retention_in_days                       = 6
}

resource "azurerm_mssql_database_extended_auditing_policy" "good_example" {
  database_id                             = azurerm_mssql_database.example.id
  retention_in_days                       = 90
}

resource "azurerm_mssql_server_extended_auditing_policy" "bad_example" {
  server_id                             = azurerm_mssql_server.example.id
  retention_in_days                       = 5
}

resource "azurerm_mssql_server_extended_auditing_policy" "bad_example" {
  server_id                             = azurerm_mssql_server.example.id
  retention_in_days                       = "something"
}

resource "azurerm_mssql_server_extended_auditing_policy" "good_example" {
  server_id                             = azurerm_mssql_server.example.id
  retention_in_days                       = 90
}
