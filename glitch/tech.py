from enum import Enum

class Tech(str, Enum):
    ansible = "ansible"
    chef = "chef"
    puppet = "puppet"

class ScriptType(str, Enum):
    script = "script"
    tasks = "tasks"
    vars = "vars"