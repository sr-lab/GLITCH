from enum import Enum
from typing import List


class Tech(Enum):
    def __init__(self, tech: str, extensions: List[str]):
        self.tech = tech
        self.extensions = extensions

    ansible = "ansible", ["yml", "yaml"]
    chef = "chef", ["rb"]
    puppet = "puppet", ["pp"]
    terraform = "terraform", ["tf"]
    docker = "docker", ["Dockerfile"]
    gha = "github-actions", ["yml", "yaml"]
