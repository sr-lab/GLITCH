resource "aws_mq_broker" "bad_example" {
  logs {
    audit = true
  }
}

resource "aws_mq_broker" "bad_example2" {
  logs {
    audit = true
    general = false
  }
}

resource "aws_mq_broker" "good_example" {
  logs {
    audit = true
    general = true
  }
}
