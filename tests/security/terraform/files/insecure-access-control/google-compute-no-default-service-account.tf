resource "google_compute_instance" "bad_example" {
  metadata {
    block-project-ssh-keys = true
  }
  boot_disk {
    kms_key_self_link = "something"
  }
}

resource "google_compute_instance" "bad_example2" {
  metadata {
    block-project-ssh-keys = true
  }
  boot_disk {
    kms_key_self_link = "something"
  }
  service_account {
    scopes = ["userinfo-email", "compute-ro", "storage-ro"]
    email  = "0123456789-compute@developer.gserviceaccount.com"
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
    scopes = ["userinfo-email", "compute-ro", "storage-ro"]
    email  = "example@email.com"
  }
}
