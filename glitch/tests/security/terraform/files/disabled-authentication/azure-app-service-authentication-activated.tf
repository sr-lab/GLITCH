resource "azurerm_app_service" "bad_example" {
  client_cert_enabled = true
  https_only = true
}

resource "azurerm_app_service" "bad_example2" {
  https_only = true
  client_cert_enabled = true

  auth_settings {
    enabled = false
  }
}

resource "azurerm_app_service" "good_example" {
  https_only = true
  client_cert_enabled = true

  auth_settings {
    enabled = true
  }
}

resource "azurerm_function_app" "good_example" {
  name                = "example-app-service"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  app_service_plan_id = azurerm_app_service_plan.example.id
  https_only = true

  auth_settings {
    enabled = true
  }
}