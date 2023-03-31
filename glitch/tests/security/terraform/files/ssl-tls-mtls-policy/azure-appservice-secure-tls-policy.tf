resource "azurerm_app_service" "bad_example" {
  site_config {
    min_tls_version = "1.0"
  }

  client_cert_enabled = true
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

resource "azurerm_app_service" "good_example2" {
  site_config {
    min_tls_version = "1.2"
  }

  client_cert_enabled = true
  https_only                 = true
  auth_settings {
    enabled = true
  }
}
