resource "google_sql_database_instance" "bad_example" {
  ip_configuration {
    require_ssl = true
  }
  settings {
    ip_configuration {
      ipv4_enabled = false
      authorized_networks {
        value           = "108.12.12.0/24"
        name            = "internal"
      }

      authorized_networks {
        value           = "0.0.0.0/0"
        name            = "internet"
      }
    }
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

resource "google_sql_database_instance" "good_example" {
  ip_configuration {
    require_ssl = true
  }
  settings {
    ip_configuration {
      ipv4_enabled = false
      authorized_networks {
        value           = "10.0.0.1/24"
        name            = "internal"
      }
    }
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
