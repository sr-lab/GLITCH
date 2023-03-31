resource "aws_api_gateway_domain_name" "bad_example" {
}

resource "aws_api_gateway_domain_name" "bad_example2" {
  security_policy = "TLS_1_0"
}

resource "aws_api_gateway_domain_name" "good_example" {
  security_policy = "TLS_1_2"
}
