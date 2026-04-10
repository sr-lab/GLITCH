resource "azurerm_postgresql_configuration" "bad_example" {
  name                = "log_connections"
  server_name         = azurerm_postgresql_server.example.name
  resource_group_name = azurerm_resource_group.example.name
  value               = "off"
}

resource "azurerm_postgresql_configuration" "bad_example2" {
  name                = "connection_throttling"
  server_name         = azurerm_postgresql_server.example1.name
  resource_group_name = azurerm_resource_group.example.name
  value               = "off"
}

resource "azurerm_postgresql_configuration" "bad_example3" {
  name                = "log_checkpoints"
  server_name         = azurerm_postgresql_server.example2.name
  resource_group_name = azurerm_resource_group.example.name
  value               = "off"
}

resource "azurerm_postgresql_configuration" "good_example" {
  name                = "log_checkpoints"
  server_name         = azurerm_postgresql_server.example3.name
  resource_group_name = azurerm_resource_group.example.name
  value               = "on"
}
