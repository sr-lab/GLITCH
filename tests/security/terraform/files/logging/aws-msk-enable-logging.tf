resource "aws_msk_cluster" "bad_example" {
  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}

resource "aws_msk_cluster" "bad_example2" {
  logging_info {
    broker_logs {
      firehose {
        enabled = false
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}

resource "aws_msk_cluster" "good_example" {
  logging_info {
    broker_logs {
      firehose {
        enabled = true
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}

resource "aws_msk_cluster" "bad_example3" {
  logging_info {
    broker_logs {
      firehose {
        enabled = false
      }
      s3 {
        enabled = false
      }
      cloudwatch_logs {
        enabled = false
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}

resource "aws_msk_cluster" "good_example2" {
  logging_info {
    broker_logs {
      firehose {
        enabled = false
      }
      s3 {
        enabled = true
      }
      cloudwatch_logs {
        enabled = true
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}
