import click

from thesis.parsers.cmof import AnsibleParser, ChefParser

@click.command()
@click.option('--tech',
        type=click.Choice(['ansible', 'chef'], case_sensitive=False), required=True)
@click.option('--unitblock', is_flag=True, default=False)
@click.argument('path', type=click.Path(exists=True))
def analysis(tech, path, unitblock):
    parser = None
    if tech == "ansible":
        parser = AnsibleParser()
    elif tech == "chef":
        parser = ChefParser()

    print(parser.parse(path, unitblock))

analysis(prog_name='#TODO')
