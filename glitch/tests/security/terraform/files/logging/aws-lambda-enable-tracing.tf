resource "aws_lambda_function" "bad_example" {
}

resource "aws_lambda_function" "bad_example2" {
  tracing_config {
    mode = "PassThrough"
  }
}

resource "aws_lambda_function" "good_example" {
  tracing_config {
    mode = "Active"
  }
}