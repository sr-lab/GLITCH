resource "azurerm_linux_virtual_machine" "bad_linux_example" {
  disable_password_authentication = false
}

resource "azurerm_linux_virtual_machine" "good_linux_example" {
}

resource "azurerm_linux_virtual_machine" "good_linux_example2" {
  disable_password_authentication = true
}


resource "azurerm_virtual_machine" "bad_example" {
}

resource "azurerm_virtual_machine" "bad_example" {
  os_profile_linux_config {
    disable_password_authentication = false
  }
}

resource "azurerm_virtual_machine" "good_example" {
  os_profile_linux_config {
    disable_password_authentication = true
  }
}
