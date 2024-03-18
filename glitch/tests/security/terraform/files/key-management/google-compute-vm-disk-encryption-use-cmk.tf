resource "google_compute_instance" "bad_example" {
  metadata = {
    block-project-ssh-keys = true
  }
  service_account {
    email  = google_service_account.default.email
  }
}

resource "google_compute_instance" "bad_example2" {
  boot_disk {
    kms_key_self_link = ""
  }

  metadata = {
    block-project-ssh-keys = true
  }
  service_account {
    email  = google_service_account.default.email
  }
}

resource "google_compute_instance" "good_example" {
  boot_disk {
    kms_key_self_link = "something"
  }

  metadata = {
    block-project-ssh-keys = true
  }
  service_account {
    email  = google_service_account.default.email
  }
}
