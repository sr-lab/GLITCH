resource "azurerm_function_app" "bad_example" {
  auth_settings {
    enabled = true
  }
}

resource "azurerm_function_app" "bad_example2" {
  https_only                 = false

  auth_settings {
    enabled = true
  }
}

resource "azurerm_function_app" "good_example" {
  https_only                 = true

  auth_settings {
    enabled = true
  }
}
