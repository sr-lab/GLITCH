resource "google_compute_instance" "bad_example" {
  shielded_instance_config {
    enable_vtpm = false
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
  shielded_instance_config {
    enable_vtpm = true
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
