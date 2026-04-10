variable "password" {
  description = "The root password for our VM"
  type        = string
  default     = "p4ssw0rd"
}

resource "evil_corp" "bad_example" {
  root_password = var.password
}

variable "password2" {
  description = "The root password for our VM"
  type        = string
}

resource "evil_corp" "good_example" {
  root_password = var.password2
}
