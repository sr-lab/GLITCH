resource "azurerm_network_security_rule" "bad_example" {
  name                        = "bad_example_security_rule"
  direction                   = "Inbound"
  access                      = "allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range     = "3389"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
}

resource "azurerm_network_security_rule" "good_example" {
  name                        = "bad_example_security_rule"
  access                      = "allow"
  direction                   = "Inbound"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range     = "3389"
  source_address_prefix       = "1.2.3.4"
  destination_address_prefix  = "*"
}

resource "azurerm_network_security_group" "bad_example2" {
  security_rule {
    name                       = "test123"
    priority                   = 100
    access                     = "allow"
    direction                  = "Inbound"
    protocol                   = "tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_security_group" "good_example2" {
  security_rule {
    name                       = "test123"
    access                     = "allow"
    priority                   = 100
    direction                  = "Inbound"
    protocol                   = "tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = "1.2.3.4"
    destination_address_prefix = "*"
  }
}