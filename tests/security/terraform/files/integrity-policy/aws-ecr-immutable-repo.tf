resource "aws_ecr_repository" "bad_example" {
  encryption_configuration {
    encryption_type = "KMS"
    kms_key = aws_kms_key.ecr_kms.key_id
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "bad_example2" {
  image_tag_mutability = "MUTABLE"
  
  encryption_configuration {
    encryption_type = "KMS"
    kms_key = aws_kms_key.ecr_kms.key_id
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "good_example" {
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key = aws_kms_key.ecr_kms.key_id
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}
