resource "google_storage_bucket" "bad_example" {
  encryption {
    default_kms_key_name = "something"
  }
}

resource "google_storage_bucket" "bad_example2" {
  uniform_bucket_level_access = false
  encryption {
    default_kms_key_name = "something"
  }
}

resource "google_storage_bucket" "good_example" {
  uniform_bucket_level_access = true
  encryption {
    default_kms_key_name = "something"
  }
}
