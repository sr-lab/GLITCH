resource "azurerm_key_vault_key" "bad_example" {
}

resource "azurerm_key_vault_key" "bad_example2" {
  expiration_date = ""
}

resource "azurerm_key_vault_key" "good_example" {
  expiration_date = "1990-12-31T00:00:00Z"
}
