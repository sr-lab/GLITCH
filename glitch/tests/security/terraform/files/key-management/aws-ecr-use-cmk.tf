resource "aws_ecr_repository" "bad_example" {
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
  }
}

resource "aws_ecr_repository" "bad_example2" {
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key = ""
  }
}

resource "aws_ecr_repository" "good_example" {
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key = aws_kms_key.ecr_kms.key_id
  }
}
