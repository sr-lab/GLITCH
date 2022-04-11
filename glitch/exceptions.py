import sys

EXCEPTIONS = {
    "ANSIBLE_PLAYBOOK": "Ansible - File is not a playbook: {}",
    "ANSIBLE_TASKS_FILE": "Ansible - File is not a tasks file: {}",
    "ANSIBLE_VARS_FILE": "Ansible - File is not a variables file: {}",
    "CHEF_COULD_NOT_PARSE": "Chef - Could not parse file: {}",
    "PUPPET_COULD_NOT_PARSE": "Puppet - Could not parse file: {}"
}

def throw_exception(exception, *args):
    print(exception.format(*args), file=sys.stderr)