resource "aws_mq_broker" "bad_example" {
  publicly_accessible = true
  logs {
    general = true
    audit = true
  }
}

resource "aws_mq_broker" "good_example" {
  logs {
    general = true
    audit = true
  }
}

resource "aws_mq_broker" "good_example2" {
  publicly_accessible = false
  logs {
    general = true
    audit = true
  }
}
