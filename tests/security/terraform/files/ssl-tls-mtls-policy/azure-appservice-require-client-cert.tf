resource "azurerm_app_service" "bad_example" {
  https_only                 = true
  auth_settings {
    enabled = true
  }
}

resource "azurerm_app_service" "bad_example2" {
  client_cert_enabled = false
  https_only                 = true
  auth_settings {
    enabled = true
  }
}

resource "azurerm_app_service" "good_example" {
  client_cert_enabled = true
  https_only                 = true
  auth_settings {
    enabled = true
  }
}
