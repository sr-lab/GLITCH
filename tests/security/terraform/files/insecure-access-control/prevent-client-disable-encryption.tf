resource "aws_athena_workgroup" "bad_example" {
  configuration {
    result_configuration {
      encryption_configuration {
        encryption_option = "sse_kms"
      }
    }
  }
}

resource "aws_athena_workgroup" "bad_example2" {
  configuration {
    enforce_workgroup_configuration    = false
    result_configuration {
      encryption_configuration {
        encryption_option = "sse_kms"
      }
    }
  }
}

resource "aws_athena_workgroup" "good_example" {
  configuration {
    enforce_workgroup_configuration    = true
    result_configuration {
      encryption_configuration {
        encryption_option = "sse_kms"
      }
    }
  }
}