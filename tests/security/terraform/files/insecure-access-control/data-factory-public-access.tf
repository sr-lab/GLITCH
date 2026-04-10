resource "azurerm_data_factory" "bad_example" {
}

resource "azurerm_data_factory" "bad_example" {
  public_network_enabled = true
}

resource "azurerm_data_factory" "good_example" {
  public_network_enabled = false
}
