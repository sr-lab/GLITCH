from enum import Enum


class Tech(str, Enum):
    ansible = "ansible"
    chef = "chef"
    puppet = "puppet"
    terraform = "terraform"
    docker = "docker"
    gha = "github-actions"
