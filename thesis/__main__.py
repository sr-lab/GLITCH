import click

from thesis.parsers.cmof import AnsibleParser, ChefParser

@click.command()
@click.option('--tech',
        type=click.Choice(['ansible', 'chef'], case_sensitive=False), required=True)
@click.argument('path', type=click.Path(exists=True))
def analysis(tech, path):
    parser = None
    if tech == "ansible":
        parser = AnsibleParser()
    elif tech == "chef":
        parser = ChefParser()
    print(parser.parse(path))

analysis(prog_name='#TODO')
