resource "google_compute_instance" "bad_example" {
  metadata = {
    block-project-ssh-keys = true
    serial-port-enable = true
  }
  service_account {
    email  = google_service_account.default.email
  }
  boot_disk {
    kms_key_self_link = "something"
  }
}

resource "google_compute_instance" "good_example" {
  metadata = {
    block-project-ssh-keys = true
  }
  service_account {
    email = google_service_account.default.email
  }
  boot_disk {
    kms_key_self_link = "somethingg"
  }
}

resource "google_compute_instance" "good_example2" {
  metadata = {
    block-project-ssh-keys = true
    serial-port-enable = false
  }
  service_account {
    email = google_service_account.default.email
  }
  boot_disk {
    kms_key_self_link = "somethinggg"
  }
}
