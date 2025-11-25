resource "aws_api_gateway_method_settings" "bad_example" {
}

resource "aws_api_gateway_method_settings" "bad_example" {
  settings {
    cache_data_encrypted = false
  }
}

resource "aws_api_gateway_method_settings" "bad_example" {
  settings {
    cache_data_encrypted = true
  }
}
