resource "aws_apigatewayv2_stage" "bad_example" {
}

resource "aws_api_gateway_stage" "bad_example" {
  xray_tracing_enabled = true
}

resource "aws_apigatewayv2_stage" "bad_example2" {
  access_log_settings {
    destination_arn = ""
    format          = "json"
  }
}

resource "aws_api_gateway_stage" "bad_example2" {
  access_log_settings {
    destination_arn = ""
    format          = "json"
  }

  xray_tracing_enabled = true
}

resource "aws_apigatewayv2_stage" "good_example" {
  access_log_settings {
    destination_arn = "arn:aws:logs:region:0123456789:log-group:access_logging"
    format          = "json"
  }
}

resource "aws_api_gateway_stage" "good_example" {
  access_log_settings {
    destination_arn = "arn:aws:logs:region:0123456789:log-group:access_logging"
    format          = "json"
  }

  xray_tracing_enabled = true
}
