resource "aws_lambda_permission" "bad_example" {
  statement_id = "AllowExecutionFromSNS"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.func.function_name
  principal = "sns.amazonaws.com"
}

resource "aws_lambda_permission" "good_example" {
  statement_id = "AllowExecutionFromSNS"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.func.function_name
  principal = "sns.amazonaws.com"
  source_arn = aws_sns_topic.default.arn
}
