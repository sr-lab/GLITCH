import click
from thesis.analysis.rules import SecurityVisitor
from thesis.parsers.cmof import AnsibleParser, ChefParser

@click.command()
@click.option('--tech',
        type=click.Choice(['ansible', 'chef'], case_sensitive=False), required=True)
@click.option('--module', is_flag=True, default=False)
@click.argument('path', type=click.Path(exists=True))
def analysis(tech, path, module):
    parser = None
    if tech == "ansible":
        parser = AnsibleParser()
    elif tech == "chef":
        parser = ChefParser()

    # FIXME Might have performance issues
    module = parser.parse(path, module)
    analysis = SecurityVisitor()
    for error in analysis.check_module(module):
        print(error)

analysis(prog_name='#TODO')
