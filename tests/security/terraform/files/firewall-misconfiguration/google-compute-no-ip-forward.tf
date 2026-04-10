resource "google_compute_instance" "bad_example" {
  can_ip_forward = true

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

resource "google_compute_instance" "good_example2" {
  can_ip_forward = false
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
