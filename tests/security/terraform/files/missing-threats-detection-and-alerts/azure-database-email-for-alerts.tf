resource "azurerm_mssql_server_security_alert_policy" "bad_example" {
  email_addresses = []

  email_account_admins = true
  retention_days = 20
}

resource "azurerm_mssql_server_security_alert_policy" "good_example" {
  email_addresses = ["db-security@acme.org"]

  email_account_admins = true
  retention_days = 20
}
