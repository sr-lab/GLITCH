resource "azurerm_virtual_machine" "bad_example" {
  os_profile {
    custom_data =<<EOF
      export DATABASE_PASSWORD=\"SomeSortOfPassword\"
      EOF
  }
  os_profile_linux_config {
    disable_password_authentication = true
  }
}

resource "azurerm_virtual_machine" "good_example" {
  os_profile {
    custom_data =<<EOF
      export GREETING="Hello there"
      EOF
  }
  os_profile_linux_config {
    disable_password_authentication = true
  }
}
