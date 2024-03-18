resource "google_sql_database_instance" "bad_example" {
  settings{
    ip_configuration {
      require_ssl = true
    }
  }
  settings {
    database_flags {
      name  = "contained database authentication"
      value = "off"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    database_flags {
      name  = "log_temp_files"
      value = "0"
    }
    database_flags {
      name  = "log_min_messages"
      value = "WARNING"
    }
    database_flags {
      name  = "log_min_duration_statement"
      value = "-1"
    }
  }
}

resource "google_sql_database_instance" "bad_example2" {
  settings{
    ip_configuration {
      require_ssl = true
    }
  }
  settings {
    database_flags {
      name  = "cross db ownership chaining"
    }
    database_flags {
      name  = "contained database authentication"
      value = "off"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    database_flags {
      name  = "log_temp_files"
      value = "0"
    }
    database_flags {
      name  = "log_min_messages"
      value = "WARNING"
    }
    database_flags {
      name  = "log_min_duration_statement"
      value = "-1"
    }
  }
}

resource "google_sql_database_instance" "bad_example3" {
  settings{
    ip_configuration {
      require_ssl = true
    }
  }
  settings {
    database_flags {
      name  = "cross db ownership chaining"
      value = "on"
    }
    database_flags {
      name  = "contained database authentication"
      value = "off"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    database_flags {
      name  = "log_temp_files"
      value = "0"
    }
    database_flags {
      name  = "log_min_messages"
      value = "WARNING"
    }
    database_flags {
      name  = "log_min_duration_statement"
      value = "-1"
    }
  }
}

resource "google_sql_database_instance" "good_example" {
  settings{
    ip_configuration {
      require_ssl = true
    }
  }
  settings {
    database_flags {
      name  = "cross db ownership chaining"
      value = "off"
    }
    database_flags {
      name  = "contained database authentication"
      value = "off"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    database_flags {
      name  = "log_temp_files"
      value = "0"
    }
    database_flags {
      name  = "log_min_messages"
      value = "WARNING"
    }
    database_flags {
      name  = "log_min_duration_statement"
      value = "-1"
    }
  }
}
