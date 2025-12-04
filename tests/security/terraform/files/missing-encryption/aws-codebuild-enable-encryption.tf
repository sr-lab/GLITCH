resource "aws_codebuild_project" "bad_example" {
  artifacts {
    encryption_disabled = true
  }
}

resource "aws_codebuild_project" "bad_example" {
  secondary_artifacts {
    encryption_disabled = true
  }
}


resource "aws_codebuild_project" "good_example1" {
  artifacts {
    encryption_disabled = false
  }
}

resource "aws_codebuild_project" "good_example2" {
  artifacts {
  }
}

resource "aws_codebuild_project" "good_example3" {
  secondary_artifacts {
    encryption_disabled = false
  }
}

resource "aws_codebuild_project" "good_example4" {
  secondary_artifacts {
  }
}
