resource "azurerm_postgresql_server" "good_example" {
  ssl_enforcement_enabled = true
}

resource "azurerm_postgresql_server" "bad_example" {
  public_network_access_enabled    = true
  ssl_enforcement_enabled = true
}

resource "azurerm_postgresql_server" "good_example" {
  public_network_access_enabled    = false
  ssl_enforcement_enabled = true
}
