resource "azurerm_mssql_server_security_alert_policy" "bad_example" {
  retention_days = 20
  email_addresses = ["db-security@acme.org"]
}

resource "azurerm_mssql_server_security_alert_policy" "bad_example2" {
  email_account_admins = false

  retention_days = 20
  email_addresses = ["db-security@acme.org"]
}

resource "azurerm_mssql_server_security_alert_policy" "good_example" {
  email_account_admins = true

  retention_days = 20
  email_addresses = ["db-security@acme.org"]
}
