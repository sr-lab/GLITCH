resource "azurerm_synapse_workspace" "bad_example" {
}

resource "azurerm_synapse_workspace" "bad_example2" {
  managed_virtual_network_enabled     = false
}

resource "azurerm_synapse_workspace" "good_example" {
  managed_virtual_network_enabled     = true
}
