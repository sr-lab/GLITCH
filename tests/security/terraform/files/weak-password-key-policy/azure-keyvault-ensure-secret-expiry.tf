resource "azurerm_key_vault_secret" "bad_example" {
  name         = "secret-sauce"
  value        = "szechuan"
  key_vault_id = azurerm_key_vault.example.id
}

resource "azurerm_key_vault_secret" "bad_example2" {
  name            = "secret-sauce"
  value           = "szechuan"
  key_vault_id    = azurerm_key_vault.example.id
  expiration_date = ""
}

resource "azurerm_key_vault_secret" "good_example" {
  name            = "secret-sauce"
  value           = "szechuan"
  key_vault_id    = azurerm_key_vault.example.id
  expiration_date = "1982-12-31T00:00:00Z"
}
