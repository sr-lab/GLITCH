resource "azurerm_security_center_contact" "bad_example" {
  email = "bad_contact@example.com"

  alert_notifications = true
  alerts_to_admins = true
}

resource "azurerm_security_center_contact" "bad_example2" {
  email = "bad_contact@example.com"
  phone = ""

  alert_notifications = true
  alerts_to_admins = true
}

resource "azurerm_security_center_contact" "good_example" {
  email = "good_contact@example.com"
  phone = "+1-555-555-5555"

  alert_notifications = true
  alerts_to_admins = true
}
