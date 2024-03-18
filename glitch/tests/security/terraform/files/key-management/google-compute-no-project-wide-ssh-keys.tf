resource "google_compute_instance" "bad_example" {
  boot_disk {
    kms_key_self_link = "something"  
  }
  service_account {
    email  = google_service_account.default.email
  }
}

resource "google_compute_instance" "bad_example2" {
  metadata = {
    block-project-ssh-keys = false
  }
  boot_disk {
    kms_key_self_link = "somethingg"  
  }
  service_account {
    email  = google_service_account.default.email
  }
}

resource "google_compute_instance" "good_example" {
  metadata = {
    block-project-ssh-keys = true
  }
  boot_disk {
    kms_key_self_link = "somethingggg"  
  }
  service_account {
    email  = google_service_account.default.email
  }
}
