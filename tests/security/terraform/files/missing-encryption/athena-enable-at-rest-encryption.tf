resource "aws_athena_database" "bad_example" {
}

resource "aws_athena_database" "good_example" {
  encryption_configuration {
    encryption_option = "SSE_S3"
  }
}

resource "aws_athena_workgroup" "bad_example" {
}

resource "aws_athena_workgroup" "good_example" {
  name = "example"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    result_configuration {
      output_location = "s3://${aws_s3_bucket.example.bucket}/output/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}
