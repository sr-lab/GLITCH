resource "azurerm_mssql_server_security_alert_policy" "bad_example" {
  disabled_alerts = ["Sql_Injection", "Data_Exfiltration"]

  retention_days = 20
  email_addresses = ["db-security@acme.org"]
  email_account_admins = true
}

resource "azurerm_mssql_server_security_alert_policy" "good_example" {
  disabled_alerts = []
  
  retention_days = 20
  email_addresses = ["db-security@acme.org"]
  email_account_admins = true
}

resource "azurerm_mssql_server_security_alert_policy" "good_example2" {
  retention_days = 20
  email_addresses = ["db-security@acme.org"]
  email_account_admins = true
}