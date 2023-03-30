resource "aws_msk_cluster" "bad_example" {
  logging_info {
    broker_logs {
      s3 {
        enabled = true
      }
    }
  }
}

resource "aws_msk_cluster" "bad_example2" {
  encryption_info {
    encryption_in_transit {
      client_broker = "TLS_PLAINTEXT"
      in_cluster = false
    }
  }

  logging_info {
    broker_logs {
      s3 {
        enabled = true
      }
    }
  }
}

resource "aws_msk_cluster" "good_example" {
  encryption_info {
    encryption_in_transit {
    }
  }

  logging_info {
    broker_logs {
      s3 {
        enabled = true
      }
    }
  }
}

resource "aws_msk_cluster" "good_example2" {
  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }

  logging_info {
    broker_logs {
      s3 {
        enabled = true
      }
    }
  }
}
