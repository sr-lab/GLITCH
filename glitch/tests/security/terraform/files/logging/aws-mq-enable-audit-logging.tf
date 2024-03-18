resource "aws_mq_broker" "bad_example" {
  logs {
    general = true
  }
}

resource "aws_mq_broker" "bad_example2" {
  logs {
    general = true
    audit = false
  }
}

resource "aws_mq_broker" "good_example" {
  logs {
    general = true
    audit = true
  }
}
