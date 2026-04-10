resource "google_compute_instance" "bad_example" {
  network_interface {
    network = "default"
    access_config {
    }
  }

  metadata {
    block-project-ssh-keys = true
  }
  boot_disk {
    kms_key_self_link = "something"
  }
  service_account {
    email  = "example@email.com"
  }
}

resource "google_compute_instance" "good_example" {
  network_interface {
    network = "default"
  }

  metadata {
    block-project-ssh-keys = true
  }
  boot_disk {
    kms_key_self_link = "something"
  }
  service_account {
    email  = "example@email.com"
  }
}
