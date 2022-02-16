from thesis.parsers.cmof import *

parser = AnsibleParser()
print(parser.parse("thesis/examples/ansible/ansible_virtualization/roles/docker"))