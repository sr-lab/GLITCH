resource "azurerm_network_security_rule" "bad_example" {
  direction = "Inbound"
  destination_address_prefix = "0.0.0.0/0"
  access = "Allow"
}

resource "azurerm_network_security_rule" "good_example" {
  direction = "Inbound"
  destination_address_prefix = "10.0.0.0/16"
  access = "Allow"
}
