from enum import Enum

class Tech(str, Enum):
    ansible = "ansible"
    chef = "chef"
    puppet = "puppet"