import sys
import traceback

from typing import List

EXCEPTIONS = {
    "ANSIBLE_PLAYBOOK": "Ansible - File is not a playbook: {}",
    "ANSIBLE_TASKS_FILE": "Ansible - File is not a tasks file: {}",
    "ANSIBLE_VARS_FILE": "Ansible - File is not a variables file: {}",
    "ANSIBLE_FILE_TYPE": "Ansible - Cannot detect file type: {}",
    "ANSIBLE_COULD_NOT_PARSE": "Ansible - Could not parse file: {}",
    "CHEF_COULD_NOT_PARSE": "Chef - Could not parse file: {}",
    "GHA_COULD_NOT_PARSE": "Github Actions Workflow - Could not parse file: {}",
    "PUPPET_COULD_NOT_PARSE": "Puppet - Could not parse file: {}",
    "DOCKER_NOT_IMPLEMENTED": "Docker - Could not parse: {}",
    "DOCKER_UNKNOW_ERROR": "Docker - Unknown Error: {}",
    "SHELL_COULD_NOT_PARSE": "Shell Command - Could not parse: {}",
    "TERRAFORM_COULD_NOT_PARSE": "Terraform - Could not parse file: {}",
}


def throw_exception(exception: str, *args: str) -> None:
    print("Error:", exception.format(*args), file=sys.stderr)
    print("=" * 20 + " Traceback " + "=" * 20, file=sys.stderr)
    exc: List[str] = traceback.format_exc().split("\n")
    if len(exc) > 40:
        exc = exc[:20] + ["..."] + exc[-20:]
    print("\n".join(exc), file=sys.stderr)
    print("=" * 51, file=sys.stderr)
