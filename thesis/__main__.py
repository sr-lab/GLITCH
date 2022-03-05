from thesis.parsers.cmof import ChefParser

parser = ChefParser()
print(parser.parse("thesis/examples/chef/nginx"))
