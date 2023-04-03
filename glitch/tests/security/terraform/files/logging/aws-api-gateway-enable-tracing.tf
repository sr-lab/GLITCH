resource "aws_api_gateway_stage" "bad_example" {
  access_log_settings {
    destination_arn = "arn:aws:logs:region:0123456789:log-group:access_logging"
    format          = "json"
  }
}

resource "aws_api_gateway_stage" "bad_example2" {
  xray_tracing_enabled = false

  access_log_settings {
    destination_arn = "arn:aws:logs:region:0123456789:log-group:access_logging"
    format          = "json"
  }
}


resource "aws_api_gateway_stage" "good_example" {
  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = "arn:aws:logs:region:0123456789:log-group:access_logging"
    format          = "json"
  }
}
