from thesis.parsers.cmof import *

parser = AnsibleParser()
print(parser.parse("thesis/examples/ansible/webserver.yaml"))